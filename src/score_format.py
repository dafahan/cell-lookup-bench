"""Cross-family table-format analysis.

Answers: does markdown really beat CSV/HTML for reading tables, and is that
family-dependent? Scores every model x {markdown, verbalized, CSV, HTML,
markdown+CoT} on the n=60 lookup set and runs the paired tests against markdown.

Reuses the canonical scoring semantics from score.py (last JAWABAN span,
normalized amounts, Wilson CI, McNemar exact) so numbers are comparable with
score_family.py.

Usage:  python src/score_format.py
Writes: results/summary_format.md (+ prints it)
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

from score import answer_span, extract_amounts, mcnemar_exact, wilson_ci
from score_family import FAMILY_ORDER, MAIN_IDS, MODEL_META, score_record

ROOT = Path(__file__).resolve().parent.parent

CONDS = ["c1_markdown", "c2_verbalized", "c3_csv", "c4_html", "c5_markdown_cot"]
LABEL = {
    "c1_markdown": "Markdown",
    "c2_verbalized": "Verbalized",
    "c3_csv": "CSV",
    "c4_html": "HTML",
    "c5_markdown_cot": "Md+CoT",
}
SCALE_ORDER = ["small", "large"]


def load() -> dict:
    """(family, scale) -> condition -> {id: record}, restricted to the lookup set."""
    grid: dict = defaultdict(lambda: defaultdict(dict))
    for path in sorted(glob.glob(str(ROOT / "results" / "run_*.json"))):
        try:
            records = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(records, list):
            continue
        for r in records:
            meta = MODEL_META.get(r.get("model", ""))
            if not meta or r.get("condition") not in CONDS:
                continue
            if r["id"] not in MAIN_IDS:  # lookup set only
                continue
            family, scale, _, splits = meta
            if "main" not in splits:
                continue
            grid[(family, scale)][r["condition"]][r["id"]] = r
    return grid


def pct(recs: dict) -> str:
    if not recs:
        return "—"
    k, n = sum(score_record(r) for r in recs.values()), len(recs)
    lo, hi = wilson_ci(k, n)
    return f"{k / n:.0%} [{lo:.0%},{hi:.0%}]"


def main() -> None:
    grid = load()
    out = ["# Table format across families (lookup set, n=60)", ""]
    out += ["Exact match per representation. CI = Wilson 95%.", ""]

    head = "| Family | Scale | " + " | ".join(LABEL[c] for c in CONDS) + " |"
    out += [head, "|" + "---|" * (len(CONDS) + 2)]
    for family in FAMILY_ORDER:
        for scale in SCALE_ORDER:
            cells = grid.get((family, scale), {})
            if not cells:
                continue
            row = [family, scale] + [pct(cells.get(c, {})) for c in CONDS]
            out.append("| " + " | ".join(row) + " |")

    out += ["", "## Paired tests against markdown (McNemar exact)", ""]
    out += ["b = markdown correct & alternative wrong; c = the reverse.", ""]
    out += ["| Family | Scale | Comparison | b | c | p | verdict |",
            "|---|---|---|---|---|---|---|"]
    for family in FAMILY_ORDER:
        for scale in SCALE_ORDER:
            cells = grid.get((family, scale), {})
            base = cells.get("c1_markdown", {})
            if not base:
                continue
            for cond in CONDS[1:]:
                alt = cells.get(cond, {})
                if not alt:
                    continue
                ids = sorted(set(base) & set(alt))
                if not ids:
                    continue
                pairs = [(score_record(base[i]), score_record(alt[i])) for i in ids]
                b, c, p = mcnemar_exact(pairs)
                if p >= 0.05:
                    verdict = "n.s."
                elif b > c:
                    verdict = "markdown better"
                else:
                    verdict = f"{LABEL[cond]} better"
                out.append(
                    f"| {family} | {scale} | md vs {LABEL[cond]} | {b} | {c} | {p:.4f} | {verdict} |"
                )

    text = "\n".join(out) + "\n"
    (ROOT / "results" / "summary_format.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
