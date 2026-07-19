"""Analyse the 2x2 control: label alignment x value repetition.

Reads results/run_*_control.json and reports, per model, exact match in each cell
of the design plus the two marginal effects. The label-as-position account
predicts a large main effect of alignment and little of repetition; the
value-repetition account predicts the reverse.

Also reports how often a wrong answer lands on the position named by the number
in the column label — the signature the label account predicts and the
repetition account does not.

Usage:  python src/score_control.py
Writes: results/summary_control.md (+ prints it)
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

from score import extract_amounts, mcnemar_exact, wilson_ci
from score_family import score_record

ROOT = Path(__file__).resolve().parent.parent
ITEMS = {i["id"]: i for i in
         json.loads((ROOT / "data" / "benchmark_control.json").read_text())["items"]}

CELLS = ["aligned_unique", "aligned_repeated", "offset_unique", "offset_repeated"]
MODEL_ORDER = ["meta-llama/Meta-Llama-3.1-8B-Instruct",
               "mistralai/Mistral-Nemo-Instruct-2407",
               "Qwen/Qwen3.5-9B",
               "meta-llama/Llama-3.3-70B-Instruct-Turbo"]


def load() -> dict:
    """model -> condition -> {id: record}"""
    grid: dict = defaultdict(lambda: defaultdict(dict))
    for path in sorted(glob.glob(str(ROOT / "results" / "run_*_control.json"))):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for r in data:
            if r.get("id") in ITEMS:
                grid[r["model"]][r["condition"]][r["id"]] = r
    return grid


def acc(recs: dict, keep) -> tuple[int, int]:
    sub = [r for i, r in recs.items() if keep(ITEMS[i])]
    return sum(map(score_record, sub)), len(sub)


def fmt(k: int, n: int) -> str:
    if n == 0:
        return "—"
    lo, hi = wilson_ci(k, n)
    return f"{k / n:.0%} [{lo:.0%},{hi:.0%}]"


def lands_on_label_position(item: dict, response: str) -> bool:
    """Did the wrong answer come from the cell the label's number names?"""
    label_pos = int(item["column_label_number"])
    lines = [ln for ln in item["context_markdown"].splitlines()
             if ln.strip().startswith("|")]
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not cells or cells[0] != item["row"]:
            continue
        if label_pos < len(cells):
            amounts = extract_amounts(cells[label_pos])
            return bool(amounts) and next(iter(amounts)) in extract_amounts(response)
    return False


def main() -> None:
    grid = load()
    out = ["# Control experiment — label alignment x value repetition", "",
           "Markdown context, n=48 per cell. CI = Wilson 95%.", ""]

    out += ["## Exact match per cell of the 2x2", "",
            "| Model | aligned+unique | aligned+repeated | offset+unique | offset+repeated |",
            "|---|---|---|---|---|"]
    for model in [m for m in MODEL_ORDER if m in grid]:
        md = grid[model].get("c1_markdown", {})
        row = [fmt(*acc(md, lambda it, c=c: it["type"] == c)) for c in CELLS]
        out.append(f"| {model} | " + " | ".join(row) + " |")

    out += ["", "## Marginal effects (markdown)", "",
            "| Model | aligned | offset | Δ | unique | repeated | Δ |",
            "|---|---|---|---|---|---|---|"]
    for model in [m for m in MODEL_ORDER if m in grid]:
        md = grid[model].get("c1_markdown", {})
        a_k, a_n = acc(md, lambda it: it["label_alignment"] == "aligned")
        o_k, o_n = acc(md, lambda it: it["label_alignment"] == "offset")
        u_k, u_n = acc(md, lambda it: it["value_pattern"] == "unique")
        r_k, r_n = acc(md, lambda it: it["value_pattern"] == "repeated")
        d_lbl = (a_k / a_n - o_k / o_n) * 100 if a_n and o_n else float("nan")
        d_rep = (u_k / u_n - r_k / r_n) * 100 if u_n and r_n else float("nan")
        out.append(f"| {model} | {fmt(a_k, a_n)} | {fmt(o_k, o_n)} | "
                   f"**{d_lbl:+.0f} pp** | {fmt(u_k, u_n)} | {fmt(r_k, r_n)} | "
                   f"{d_rep:+.0f} pp |")

    out += ["", "## Paired tests (McNemar exact, markdown)", "",
            "| Model | comparison | b | c | p |", "|---|---|---|---|---|"]
    for model in [m for m in MODEL_ORDER if m in grid]:
        md = grid[model].get("c1_markdown", {})
        for name, key, lo_v, hi_v in [
            ("aligned vs offset", "label_alignment", "aligned", "offset"),
            ("unique vs repeated", "value_pattern", "unique", "repeated"),
        ]:
            lo = sorted(i for i in md if ITEMS[i][key] == lo_v)
            hi = sorted(i for i in md if ITEMS[i][key] == hi_v)
            pairs = [(score_record(md[a]), score_record(md[b]))
                     for a, b in zip(lo, hi)]
            if not pairs:
                continue
            b, c, p = mcnemar_exact(pairs)
            out.append(f"| {model} | {name} | {b} | {c} | {p:.4f} |")

    out += ["", "## Verbalization as positive control", "",
            "| Model | markdown | verbalized |", "|---|---|---|"]
    for model in [m for m in MODEL_ORDER if m in grid]:
        md = grid[model].get("c1_markdown", {})
        vb = grid[model].get("c2_verbalized", {})
        out.append(f"| {model} | {fmt(*acc(md, lambda it: True))} "
                   f"| {fmt(*acc(vb, lambda it: True))} |")

    out += ["", "## Signature: wrong answer lands on the label-named position", "",
            "| Model | wrong (offset cells) | of which land on label position |",
            "|---|---|---|"]
    for model in [m for m in MODEL_ORDER if m in grid]:
        md = grid[model].get("c1_markdown", {})
        wrong = [r for i, r in md.items()
                 if ITEMS[i]["label_alignment"] == "offset" and not score_record(r)]
        hits = sum(lands_on_label_position(ITEMS[r["id"]], r["response"])
                   for r in wrong)
        share = f"{hits}/{len(wrong)}" if wrong else "—"
        out.append(f"| {model} | {len(wrong)} | {share} |")

    text = "\n".join(out) + "\n"
    (ROOT / "results" / "summary_control.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
