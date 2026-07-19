"""Score benchmark runs: deterministic amount extraction, Exact Match, McNemar,
cross-model equalizer tests, and cost/latency summary.

Usage:  python src/score.py results/run_groq_*.json
Writes: results/summary.md (+ prints it)
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent

GROUPED = re.compile(r"\d{1,3}(?:[.,]\d{3})+")   # 3.000.000 / 3,000,000
PLAIN = re.compile(r"\d{5,}")                    # 3000000
JUTA = re.compile(r"(\d+(?:[.,]\d+)?)\s*juta", re.IGNORECASE)
MIN_AMOUNT = 100_000                             # filters years, group numbers, etc.

# Cross-model hypothesis tests: (label, (model_a, cond_a), (model_b, cond_b))
EQUALIZER_PAIRS = [
    ("gap dasar: 8B markdown vs 70B markdown",
     ("llama-3.1-8b-instant", "c1_markdown"), ("llama-3.3-70b-versatile", "c1_markdown")),
    ("equalizer: 8B verbalized vs 70B markdown",
     ("llama-3.1-8b-instant", "c2_verbalized"), ("llama-3.3-70b-versatile", "c1_markdown")),
]

# USD per 1M tokens, (input, output). List prices captured 2026-07-19.
#
# The cost ratio between a small and a large model is strongly provider-dependent:
# the 70B costs 5.9x more per input token on Groq than on DeepInfra, so quoting a
# single ratio would report the provider's price list as if it were a property of
# the method. Both schedules are kept and reported side by side.
PRICING_GROQ = {
    "llama-3.1-8b-instant": (0.05, 0.08),
    "llama-3.3-70b-versatile": (0.59, 0.79),
}

PRICING_DEEPINFRA = {
    # NOTE: the catalogue lists only the -Turbo SKU for Llama 3.1 8B, while the
    # runs use the non-Turbo checkpoint. Priced with the Turbo rate pending
    # confirmation; flagged in the manuscript's cost note.
    "meta-llama/Meta-Llama-3.1-8B-Instruct": (0.02, 0.03),
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": (0.10, 0.32),
    "Qwen/Qwen2.5-72B-Instruct": (0.36, 0.40),
    "Qwen/Qwen3.5-9B": (0.10, 0.15),
    "Qwen/Qwen3.5-27B": (0.26, 2.60),
    "mistralai/Mistral-Nemo-Instruct-2407": (0.019, 0.03),
    "mistralai/Mistral-Small-24B-Instruct-2501": (0.05, 0.08),
    "google/gemma-3-12b-it": (0.05, 0.15),
    "google/gemma-3-27b-it": (0.08, 0.16),
}

# Qwen2.5-7B ran on Together, the only serverless host for that checkpoint. Note
# the consequence: Together charges more for this 7B model than DeepInfra charges
# for the 72B one, so the Qwen2.5 pair is the one within-family scale comparison
# whose *cost* cannot be read across providers. Accuracy is unaffected.
PRICING_TOGETHER = {
    "Qwen/Qwen2.5-7B-Instruct-Turbo": (0.30, 0.30),
}

PRICING = {**PRICING_GROQ, **PRICING_DEEPINFRA, **PRICING_TOGETHER}


def answer_span(text: str) -> str:
    """Score only what follows the last 'JAWABAN:' marker when present."""
    idx = text.upper().rfind("JAWABAN")
    return text[idx:] if idx >= 0 else text


def extract_amounts(text: str) -> set[int]:
    text = answer_span(text).replace("*", "")
    amounts: set[int] = set()
    for m in JUTA.finditer(text):
        val = float(m.group(1).replace(",", "."))
        amounts.add(int(round(val * 1_000_000)))
    stripped = JUTA.sub(" ", text)
    for m in GROUPED.finditer(stripped):
        amounts.add(int(re.sub(r"[.,]", "", m.group(0))))
    without_grouped = GROUPED.sub(" ", stripped)
    for m in PLAIN.finditer(without_grouped):
        amounts.add(int(m.group(0)))
    return {a for a in amounts if a >= MIN_AMOUNT}


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def mcnemar_exact(pairs: list[tuple[bool, bool]]) -> tuple[int, int, float]:
    """Returns (b, c, p): b = A correct & B wrong, c = A wrong & B correct."""
    b = sum(1 for a, bb in pairs if a and not bb)
    c = sum(1 for a, bb in pairs if not a and bb)
    if b + c == 0:
        return b, c, 1.0
    p = binomtest(min(b, c), b + c, 0.5).pvalue
    return b, c, p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    args = ap.parse_args()

    paths: list[str] = []
    for pattern in args.runs:
        paths.extend(sorted(glob.glob(pattern)))
    records = []
    for path in paths:
        records.extend(json.loads(Path(path).read_text(encoding="utf-8")))

    for r in records:
        gv = r["gold_value"]
        if gv.isdigit():
            gold = int(gv)
            amounts = extract_amounts(r["response"])
            r["lenient"] = gold in amounts
            r["strict"] = amounts == {gold}
        else:
            # name-answer items (aggregation "which program" questions)
            span = answer_span(r["response"]).lower()
            r["lenient"] = gv.lower() in span
            others = [d for d in (r.get("distractors") or []) if d.lower() in span]
            r["strict"] = r["lenient"] and not others

    by_group: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        by_group[(r["model"], r["condition"])].append(r)
    # (model, condition) -> {id: record}
    idx: dict[tuple, dict[str, dict]] = {
        g: {r["id"]: r for r in rs} for g, rs in by_group.items()
    }

    lines = ["# Cell-Lookup Micro-Benchmark — Results", ""]
    lines.append("## Exact Match per condition")
    lines.append("")
    lines.append("| Model | Condition | n | Lenient EM | 95% CI | Strict EM |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for (model, cond), rs in sorted(by_group.items()):
        n = len(rs)
        k_len = sum(r["lenient"] for r in rs)
        k_str = sum(r["strict"] for r in rs)
        lo, hi = wilson_ci(k_len, n)
        lines.append(f"| {model} | {cond} | {n} | {k_len}/{n} = {k_len/n:.1%} "
                     f"| [{lo:.1%}, {hi:.1%}] | {k_str/n:.1%} |")
    lines.append("")

    lines.append("## McNemar exact (paired, lenient EM) — within model")
    lines.append("")
    lines.append("| Model | Pair | b (A✓B✗) | c (A✗B✓) | p-value |")
    lines.append("| --- | --- | --- | --- | --- |")
    models = sorted({m for m, _ in by_group})
    for model in models:
        conds = sorted(c for m, c in by_group if m == model)
        base = "c1_markdown"
        for cond in conds:
            if cond == base or (model, base) not in idx:
                continue
            ids = sorted(set(idx[(model, base)]) & set(idx[(model, cond)]))
            pairs = [(idx[(model, base)][i]["lenient"], idx[(model, cond)][i]["lenient"])
                     for i in ids]
            b, c, p = mcnemar_exact(pairs)
            sig = " **(sig.)**" if p < 0.05 else ""
            lines.append(f"| {model} | {base} vs {cond} | {b} | {c} | {p:.4f}{sig} |")
    lines.append("")

    lines.append("## Equalizer tests (cross-model, paired per question)")
    lines.append("")
    lines.append("| Test | A | B | A acc | B acc | b | c | p-value |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for label, (ma, ca), (mb, cb) in EQUALIZER_PAIRS:
        if (ma, ca) not in idx or (mb, cb) not in idx:
            continue
        ids = sorted(set(idx[(ma, ca)]) & set(idx[(mb, cb)]))
        pairs = [(idx[(ma, ca)][i]["lenient"], idx[(mb, cb)][i]["lenient"]) for i in ids]
        b, c, p = mcnemar_exact(pairs)
        acc_a = sum(a for a, _ in pairs) / len(pairs)
        acc_b = sum(bb for _, bb in pairs) / len(pairs)
        lines.append(f"| {label} | {ma}/{ca} | {mb}/{cb} "
                     f"| {acc_a:.1%} | {acc_b:.1%} | {b} | {c} | {p:.4f} |")
    lines.append("")

    lines.append("## Cost & latency (fresh calls only; cached reruns excluded from latency)")
    lines.append("")
    lines.append("| Model | Condition | mean latency (s) | tokens in/out | est. USD per 1000 queries |")
    lines.append("| --- | --- | --- | --- | --- |")
    for (model, cond), rs in sorted(by_group.items()):
        lat = [r["latency_s"] for r in rs if r.get("latency_s")]
        tin = sum(r.get("prompt_tokens", 0) for r in rs)
        tout = sum(r.get("completion_tokens", 0) for r in rs)
        n = len(rs)
        cost = ""
        if model in PRICING and n:
            pin, pout = PRICING[model]
            cost = f"${(tin/n*pin + tout/n*pout) / 1e6 * 1000:.3f}"
        mean_lat = f"{sum(lat)/len(lat):.2f}" if lat else "—"
        lines.append(f"| {model} | {cond} | {mean_lat} | {tin}/{tout} | {cost} |")
    lines.append("")

    lines.append("## Failures (lenient) — for qualitative error analysis")
    lines.append("")
    for (model, cond), rs in sorted(by_group.items()):
        fails = [r for r in rs if not r["lenient"]]
        lines.append(f"### {model} — {cond} ({len(fails)} failures)")
        for r in fails:
            resp = answer_span(r["response"]).replace("\n", " ")[:160]
            lines.append(f"- `{r['id']}` gold={r['gold_raw']} → {resp!r}")
        lines.append("")

    out = ROOT / "results" / "summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
