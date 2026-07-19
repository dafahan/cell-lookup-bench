"""Run the cell-lookup benchmark: conditions x questions against one model.

Usage:
  python src/run_bench.py --provider groq --model llama-3.1-8b-instant
  python src/run_bench.py --provider groq --model llama-3.3-70b-versatile
  python src/run_bench.py --provider ollama --model llama3:8b-instruct-q4_K_M
  python src/run_bench.py --provider groq --limit 2          # smoke test

Output: results/run_{provider}_{model}.json  (one record per item x condition)
"""

from __future__ import annotations

import argparse
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from providers import Cache, make_client  # noqa: E402

BASE_PROMPT = (
    "Jawab pertanyaan HANYA berdasarkan konteks di bawah ini. "
    "Salin angka persis seperti tertulis di konteks.\n\n"
    "Konteks:\n{context}\n\n"
    "Pertanyaan: {question}\n\n"
    "Akhiri jawabanmu dengan satu baris persis berformat:\n"
    "JAWABAN: <nilai>"
)

COT_PROMPT = (
    "Jawab pertanyaan HANYA berdasarkan konteks di bawah ini. "
    "Baca konteks baris demi baris secara perlahan, periksa setiap sel dengan teliti, "
    "dan jelaskan penalaranmu langkah demi langkah sebelum menjawab. "
    "Salin angka persis seperti tertulis di konteks.\n\n"
    "Konteks:\n{context}\n\n"
    "Pertanyaan: {question}\n\n"
    "Akhiri jawabanmu dengan satu baris persis berformat:\n"
    "JAWABAN: <nilai>"
)

# condition -> (context field, prompt template, max_tokens)
CONDITIONS = {
    "c1_markdown": ("context_markdown", BASE_PROMPT, 300),
    "c2_verbalized": ("context_verbalized", BASE_PROMPT, 300),
    "c3_csv": ("context_csv", BASE_PROMPT, 300),
    "c4_html": ("context_html", BASE_PROMPT, 300),
    "c5_markdown_cot": ("context_markdown", COT_PROMPT, 700),
    "c6_verbalized_oracle": ("context_verbalized_oracle", BASE_PROMPT, 300),
    "c7_hybrid": ("context_hybrid", BASE_PROMPT, 300),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["groq", "ollama", "deepinfra", "together"], required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--dataset", default=str(ROOT / "data" / "benchmark.json"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tag", default="", help="suffix for the output filename")
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent request threads (hosted providers allow many)")
    args = ap.parse_args()

    client = make_client(args.provider, args.model)
    cache = Cache()
    conditions = [c.strip() for c in args.conditions.split(",")]
    for c in conditions:
        if c not in CONDITIONS:
            raise SystemExit(f"unknown condition {c}; choose from {list(CONDITIONS)}")

    data = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    items = data["items"][: args.limit] if args.limit else data["items"]

    model_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", client.model)
    tag = f"_{args.tag}" if args.tag else ""
    out_path = ROOT / "results" / f"run_{client.provider}_{model_slug}{tag}.json"
    tasks = []
    for cond in conditions:
        ctx_field, template, max_tokens = CONDITIONS[cond]
        for item in items:
            prompt = template.format(context=item[ctx_field], question=item["question"])
            tasks.append((cond, item, prompt, max_tokens))

    lock = threading.Lock()
    total = len(tasks)
    counter = {"done": 0}

    def process(task: tuple) -> dict:
        cond, item, prompt, max_tokens = task
        key = Cache.key(client.provider, client.model, prompt)
        with lock:
            result = cache.get(key)
        hit = result is not None
        if result is None:
            result = client.complete(prompt, max_tokens)  # HTTP outside the lock
            with lock:
                cache.put(key, result)
        with lock:
            counter["done"] += 1
            n = counter["done"]
        mark = "(cache)" if hit else f"({result['latency_s']}s)"
        print(f"[{n}/{total}] {cond} {item['id']} {mark} "
              f"-> {result['text'][-50:]!r}", flush=True)
        return {
            "id": item["id"],
            "condition": cond,
            "provider": client.provider,
            "model": client.model,
            "question": item["question"],
            "gold_raw": item["gold_raw"],
            "gold_value": item["gold_value"],
            "type": item.get("type"),
            "distractors": item.get("distractors"),
            "response": result["text"],
            "latency_s": result["latency_s"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
        }

    if args.workers > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            records = list(ex.map(process, tasks))
    else:
        records = [process(t) for t in tasks]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out_path} ({len(records)} records)")


if __name__ == "__main__":
    main()
