"""Provider-agnostic LLM client (local-first): Ollama or Groq behind one interface.

Both providers receive the identical prompt with temperature=0. `complete()`
returns the text plus latency and token usage (for the cost/latency analysis).
Responses are cached in results/cache.json keyed by (provider, model, prompt)
hash, so interrupted or repeated runs never re-pay inference.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
# Overridable so concurrent runs can use separate cache files (avoids races on
# the shared JSON when several run_bench processes write at once).
CACHE_PATH = Path(os.getenv("BENCH_CACHE", str(ROOT / "results" / "cache.json")))

DEFAULT_MAX_TOKENS = 300


class Cache:
    def __init__(self, path: Path = CACHE_PATH):
        self.path = path
        self.data: dict[str, dict] = {}
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def key(provider: str, model: str, prompt: str) -> str:
        return hashlib.sha256(f"{provider}|{model}|{prompt}".encode()).hexdigest()

    def get(self, k: str) -> dict | None:
        v = self.data.get(k)
        return v if isinstance(v, dict) else None

    def put(self, k: str, v: dict) -> None:
        self.data[k] = v
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")


class LLMClient:
    provider: str
    model: str

    def complete(self, prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
        """Returns {text, latency_s, prompt_tokens, completion_tokens}."""
        raise NotImplementedError


class OllamaClient(LLMClient):
    provider = "ollama"

    def __init__(self, model: str | None = None):
        self.base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M")

    def complete(self, prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
        t0 = time.time()
        r = requests.post(
            f"{self.base}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "num_predict": max_tokens},
            },
            timeout=600,
        )
        r.raise_for_status()
        j = r.json()
        return {
            "text": j["response"].strip(),
            "latency_s": round(time.time() - t0, 3),
            "prompt_tokens": j.get("prompt_eval_count", 0),
            "completion_tokens": j.get("eval_count", 0),
        }


class GroqClient(LLMClient):
    provider = "groq"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    extra_body: dict = {}

    def __init__(self, model: str | None = None):
        self.key = os.getenv("GROQ_API_KEY")
        if not self.key:
            raise SystemExit("GROQ_API_KEY not set (see .env.example)")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def complete(self, prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
        last_err = "no attempt made"
        for attempt in range(8):
            t0 = time.time()
            try:
                r = requests.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0,
                        "max_tokens": max_tokens,
                        **self.extra_body,
                    },
                    timeout=120,
                )
            except requests.RequestException as e:
                last_err = f"connection error: {e}"
                time.sleep(min(2 ** attempt, 60))
                continue
            if r.status_code == 429 or r.status_code >= 500:
                last_err = f"status {r.status_code}"
                wait = float(r.headers.get("retry-after", 2 ** attempt))
                time.sleep(min(wait, 60))
                continue
            r.raise_for_status()
            j = r.json()
            usage = j.get("usage", {})
            return {
                "text": j["choices"][0]["message"]["content"].strip(),
                "latency_s": round(time.time() - t0, 3),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            }
        raise RuntimeError(f"Groq: retries exhausted ({last_err})")


class DeepInfraClient(GroqClient):
    """OpenAI-compatible fallback when Groq daily quotas run out.
    Same Llama family: meta-llama/Meta-Llama-3.1-8B-Instruct,
    meta-llama/Llama-3.3-70B-Instruct."""

    provider = "deepinfra"
    endpoint = "https://api.deepinfra.com/v1/openai/chat/completions"

    def __init__(self, model: str | None = None):
        self.key = os.getenv("DEEPINFRA_API_KEY")
        if not self.key:
            raise SystemExit("DEEPINFRA_API_KEY not set (see .env.example)")
        self.model = model or os.getenv(
            "DEEPINFRA_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
        # Qwen3.x are hybrid-reasoning; disable thinking so the model answers
        # directly instead of burning the token budget on a <think> trace.
        if "qwen3" in self.model.lower():
            self.extra_body = {"chat_template_kwargs": {"enable_thinking": False}}


class TogetherClient(GroqClient):
    """OpenAI-compatible Together AI client. Hosts the same-generation Qwen2.5
    dense pair (Qwen/Qwen2.5-7B-Instruct-Turbo, Qwen/Qwen2.5-72B-Instruct-Turbo)
    that DeepInfra no longer serves at the small end."""

    provider = "together"
    endpoint = "https://api.together.xyz/v1/chat/completions"

    def __init__(self, model: str | None = None):
        self.key = os.getenv("TOGETHER_API_KEY")
        if not self.key:
            raise SystemExit("TOGETHER_API_KEY not set (see .env.example)")
        self.model = model or os.getenv(
            "TOGETHER_MODEL", "Qwen/Qwen2.5-7B-Instruct-Turbo")


def make_client(provider: str, model: str | None = None) -> LLMClient:
    if provider == "ollama":
        return OllamaClient(model)
    if provider == "groq":
        return GroqClient(model)
    if provider == "deepinfra":
        return DeepInfraClient(model)
    if provider == "together":
        return TogetherClient(model)
    raise SystemExit(f"unknown provider: {provider}")
