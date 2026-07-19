"""Cross-family scale-equalizer analysis.

Groups every run_*.json record by (family, scale) and, per family, reports:
  - per-condition Exact Match (markdown vs verbalized) with Wilson CI,
  - scale gap:       McNemar  small/markdown   vs  large/markdown,
  - equalizer:       McNemar  small/verbalized vs  large/markdown,
  - verbalization:   McNemar  small/markdown   vs  small/verbalized.
Main (n=60 lookup) and hard (n=48 wide/multilevel/aggregation) sets are scored
separately; the hard set is additionally broken down by table type.

Splitting is by dataset id-membership (main q*, hard a*/m*/w*...), and each model
is pinned to its canonical split so the Groq-vs-DeepInfra Llama robustness runs
never pool together. Hard table type comes from benchmark_hard.json (authoritative),
so runs produced before the harness stored `type` are still classified correctly.

Usage:  python src/score_family.py results/run_*.json
Writes: results/summary_family.md (+ prints it)
"""

from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

from score import answer_span, extract_amounts, mcnemar_exact, wilson_ci

ROOT = Path(__file__).resolve().parent.parent

# raw model id -> (family, scale, contrast, {allowed splits})
MODEL_META = {
    "llama-3.1-8b-instant": ("Llama 3", "small", "~9x", {"main"}),
    "llama-3.3-70b-versatile": ("Llama 3", "large", "~9x", {"main"}),
    "meta-llama/Meta-Llama-3.1-8B-Instruct": ("Llama 3", "small", "~9x", {"hard"}),
    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": ("Llama 3", "small", "~9x", {"hard"}),
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": ("Llama 3", "large", "~9x", {"hard"}),
    "Qwen/Qwen2.5-7B-Instruct-Turbo": ("Qwen2.5", "small", "~10x", {"main", "hard"}),
    "Qwen/Qwen2.5-72B-Instruct": ("Qwen2.5", "large", "~10x", {"main", "hard"}),
    "Qwen/Qwen3.5-9B": ("Qwen3.5", "small", "~3x", {"main", "hard"}),
    "Qwen/Qwen3.5-27B": ("Qwen3.5", "large", "~3x", {"main", "hard"}),
    "mistralai/Mistral-Nemo-Instruct-2407": ("Mistral", "small", "~2x", {"main", "hard"}),
    "mistralai/Mistral-Small-24B-Instruct-2501": ("Mistral", "large", "~2x", {"main", "hard"}),
    "google/gemma-3-12b-it": ("Gemma 3", "small", "~2.3x", {"main", "hard"}),
    "google/gemma-3-27b-it": ("Gemma 3", "large", "~2.3x", {"main", "hard"}),
}

# A model pinned out of a split may still be the only source for a condition the
# pinned provider never ran: Llama's hybrid arm exists on DeepInfra only, so the
# blanket {"hard"} pin above silently dropped it from the lookup grid. Admit those
# conditions back without letting the two providers pool on any shared condition.
SPLIT_EXCEPTIONS = {
    ("meta-llama/Meta-Llama-3.1-8B-Instruct", "main"): {"c7_hybrid"},
    ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "main"): {"c7_hybrid"},
}

FAMILY_ORDER = ["Llama 3", "Qwen2.5", "Qwen3.5", "Mistral", "Gemma 3"]
CONTRAST = {m[0]: m[2] for m in MODEL_META.values()}
HARD_TYPES = ("wide", "multilevel", "aggregation", "arithmetic", "header3")

MAIN_IDS = {i["id"] for i in json.loads((ROOT / "data" / "benchmark.json").read_text())["items"]}
HARD_TYPE_BY_ID = {i["id"]: i["type"] for i in
                   json.loads((ROOT / "data" / "benchmark_hard.json").read_text())["items"]}


def score_record(r: dict) -> bool:
    """Lenient exact match, matching score.py semantics."""
    gv = r["gold_value"]
    if gv.isdigit():
        return int(gv) in extract_amounts(r["response"])
    return gv.lower() in answer_span(r["response"]).lower()


def em(rs: list[dict]) -> tuple[int, int]:
    return sum(score_record(r) for r in rs), len(rs)


def paired(a: dict[str, dict], b: dict[str, dict]) -> list[tuple[bool, bool]]:
    ids = sorted(set(a) & set(b))
    return [(score_record(a[i]), score_record(b[i])) for i in ids]


def cell(k: int, n: int) -> str:
    if n == 0:
        return "—"
    lo, hi = wilson_ci(k, n)
    return f"{k}/{n}={k/n:.0%} [{lo:.0%},{hi:.0%}]"


def mc(pairs: list[tuple[bool, bool]]) -> str:
    if not pairs:
        return "—"
    b, c, p = mcnemar_exact(pairs)
    sig = " **sig**" if p < 0.05 else ""
    return f"b={b} c={c} p={p:.4f}{sig}"


def analyze(records: list[dict], split: str, title: str, lines: list[str]) -> None:
    # index: (family, scale, condition) -> {id: record}
    idx: dict[tuple, dict[str, dict]] = defaultdict(dict)
    fams_present: set[str] = set()
    for r in records:
        meta = MODEL_META.get(r["model"])
        if not meta:
            continue
        if split not in meta[3]:
            allowed = SPLIT_EXCEPTIONS.get((r["model"], split))
            if not allowed or r["condition"] not in allowed:
                continue
        fam, scale = meta[0], meta[1]
        fams_present.add(fam)
        idx[(fam, scale, r["condition"])][r["id"]] = r

    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Family | Contrast | small md | small verb | small hyb "
                 "| large md | large verb | large hyb |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for fam in [f for f in FAMILY_ORDER if f in fams_present]:
        s_md = idx.get((fam, "small", "c1_markdown"), {})
        s_vb = idx.get((fam, "small", "c2_verbalized"), {})
        s_hy = idx.get((fam, "small", "c7_hybrid"), {})
        l_md = idx.get((fam, "large", "c1_markdown"), {})
        l_vb = idx.get((fam, "large", "c2_verbalized"), {})
        l_hy = idx.get((fam, "large", "c7_hybrid"), {})
        lines.append(
            f"| {fam} | {CONTRAST[fam]} | {cell(*em(list(s_md.values())))} "
            f"| {cell(*em(list(s_vb.values())))} | {cell(*em(list(s_hy.values())))} "
            f"| {cell(*em(list(l_md.values())))} | {cell(*em(list(l_vb.values())))} "
            f"| {cell(*em(list(l_hy.values())))} |")
    lines.append("")
    lines.append("| Family | Scale gap (S-md vs L-md) | Equalizer (S-verb vs L-md) "
                 "| Verbaliz. (S-md vs S-verb) | Verbaliz. large (L-md vs L-verb) "
                 "| Hybrid vs md (S) | Hybrid vs verb (S) |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for fam in [f for f in FAMILY_ORDER if f in fams_present]:
        s_md = idx.get((fam, "small", "c1_markdown"), {})
        s_vb = idx.get((fam, "small", "c2_verbalized"), {})
        s_hy = idx.get((fam, "small", "c7_hybrid"), {})
        l_md = idx.get((fam, "large", "c1_markdown"), {})
        l_vb = idx.get((fam, "large", "c2_verbalized"), {})
        lines.append(
            f"| {fam} | {mc(paired(s_md, l_md))} | {mc(paired(s_vb, l_md))} "
            f"| {mc(paired(s_md, s_vb))} | {mc(paired(l_md, l_vb))} "
            f"| {mc(paired(s_hy, s_md))} | {mc(paired(s_hy, s_vb))} |")
    lines.append("")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    args = ap.parse_args()
    paths: list[str] = []
    for pat in args.runs:
        paths.extend(sorted(glob.glob(pat)))
    records: list[dict] = []
    for p in sorted(set(paths)):
        records.extend(json.loads(Path(p).read_text(encoding="utf-8")))

    main_rs = [r for r in records if r["id"] in MAIN_IDS]
    hard_rs = [r for r in records if r["id"] in HARD_TYPE_BY_ID]

    lines = ["# Cross-Family Scale-Equalizer Analysis", ""]
    analyze(main_rs, "main", "Main lookup benchmark (n=60)", lines)
    analyze(hard_rs, "hard", "Hard set — all types (n=48)", lines)
    for t in HARD_TYPES:
        sub = [r for r in hard_rs if HARD_TYPE_BY_ID.get(r["id"]) == t]
        n_t = len({r["id"] for r in sub})
        analyze(sub, "hard", f"Hard set — {t} only (n={n_t})", lines)

    out = ROOT / "results" / "summary_family.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
