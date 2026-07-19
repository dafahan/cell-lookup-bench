"""Anatomy of the small-model cell-lookup failures.

Every wrong answer on the markdown lookup set is classified against the source
table: did the model return a value from the *right row but wrong column*, from
the *right column but wrong row*, or something absent from the row entirely?
Also reports failures by table width and the value-repetition density that the
column-indexing account depends on.

Usage:  python src/score_errors.py [--model llama-3.1-8b-instant]
Writes: results/summary_errors.md (+ prints it)
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from score import extract_amounts
from score_family import MODEL_META, score_record

ROOT = Path(__file__).resolve().parent.parent
ITEMS = {i["id"]: i for i in
         json.loads((ROOT / "data" / "benchmark.json").read_text())["items"]}

CELL = re.compile(r"\*\*|\s+")


def parse_table(markdown: str, row_label: str) -> tuple[list[str], list[str]] | None:
    """Return (header cells, value cells) of the row whose first cell matches."""
    header: list[str] | None = None
    for line in markdown.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):  # separator row
            continue
        if header is None or cells[0].lower() in {"program studi", "uraian", "jenis"}:
            header = cells
            continue
        if CELL.sub("", cells[0]).lower() == CELL.sub("", row_label).lower():
            return header, cells
    return None


def classify(item: dict, response: str) -> str:
    """Bucket one wrong answer by where its value sits in the source table."""
    parsed = parse_table(item["context_markdown"], item["row"])
    got = extract_amounts(response)
    if not got:
        return "no parsable answer"
    if not parsed:
        return "unclassified"
    header, cells = parsed
    gold = int(item["gold_value"])

    row_values: dict[int, int] = {}
    for idx, cell in enumerate(cells):
        amounts = extract_amounts(cell)
        if amounts:
            row_values[idx] = next(iter(amounts))
    gold_idx = next((i for i, v in row_values.items() if v == gold), None)

    for idx, value in row_values.items():
        if value in got and idx != gold_idx:
            if gold_idx is not None and abs(idx - gold_idx) == 1:
                return "adjacent column, correct row"
            return "other column, correct row"

    # not in this row: look for the value elsewhere in the same column
    if gold_idx is not None:
        for line in item["context_markdown"].splitlines():
            if not line.strip().startswith("|"):
                continue
            other = [c.strip() for c in line.strip("|").split("|")]
            if len(other) > gold_idx:
                amounts = extract_amounts(other[gold_idx])
                if amounts and next(iter(amounts)) in got:
                    return "correct column, wrong row"
    return "value absent from table"


ENCODINGS = {"c1_markdown": "Markdown", "c3_csv": "CSV",
             "c4_html": "HTML", "c5_markdown_cot": "Md+CoT"}


def cross_encoding_section(*models: str) -> list[str]:
    """Does the column-indexing error survive a change of serialization?

    The header labels are identical in every encoding, so if the failure really
    comes from reading a label's number as a position, changing pipes to commas
    or to <td> tags should not remove it.
    """
    by_model: dict[str, dict[str, dict[str, dict]]] = defaultdict(
        lambda: defaultdict(dict))
    for path in sorted(glob.glob(str(ROOT / "results" / "run_*.json"))):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, list):
            continue
        for r in data:
            if r.get("model") in models and r.get("condition") in ENCODINGS \
                    and r.get("id") in ITEMS:
                by_model[r["model"]][r["condition"]][r["id"]] = r

    out = ["", "## Does the error survive a change of encoding?", "",
           "Header labels are identical in every encoding, so the label-as-position "
           "confusion should persist if that is really the mechanism.", "",
           "| Model | Encoding | Wrong | Correct row, wrong column | On label position |",
           "|---|---|---|---|---|"]
    for model in models:
        for cond, label in ENCODINGS.items():
            recs = by_model.get(model, {}).get(cond, {})
            if not recs:
                continue
            wrong = [r for r in recs.values() if not score_record(r)]
            row_ok = on_label = 0
            for rec in wrong:
                item = ITEMS[rec["id"]]
                parsed = parse_table(item["context_markdown"], item["row"])
                got = extract_amounts(rec["response"])
                if not parsed or not got:
                    continue
                _, cells = parsed
                values = {i: next(iter(extract_amounts(c)))
                          for i, c in enumerate(cells) if extract_amounts(c)}
                gold_idx = next((i for i, v in values.items()
                                 if v == int(item["gold_value"])), None)
                answered = [i for i, v in values.items() if v in got]
                if gold_idx is None or not answered:
                    continue
                row_ok += 1
                m = re.search(r"(\d+)", item["column"])
                if m and int(m.group(1)) == answered[0]:
                    on_label += 1
            out.append(f"| {model} | {label} | {len(wrong)} | {row_ok} | {on_label} |")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="llama-3.1-8b-instant")
    args = ap.parse_args()

    records = []
    for path in sorted(glob.glob(str(ROOT / "results" / "run_*.json"))):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, list):
            continue
        records += [r for r in data
                    if r.get("model") == args.model
                    and r.get("condition") == "c1_markdown"
                    and r.get("id") in ITEMS]

    seen: dict[str, dict] = {r["id"]: r for r in records}
    wrong = [r for r in seen.values() if not score_record(r)]
    family, scale = MODEL_META.get(args.model, ("?", "?", "", set()))[:2]

    out = [f"# Failure anatomy — {family} {scale} ({args.model})", ""]
    out += [f"Markdown lookup set: {len(seen) - len(wrong)}/{len(seen)} correct, "
            f"{len(wrong)} wrong.", ""]

    buckets = Counter(classify(ITEMS[r["id"]], r["response"]) for r in wrong)
    out += ["## Where the wrong value came from", "",
            "| Bucket | n |", "|---|---|"]
    for name, n in buckets.most_common():
        out.append(f"| {name} | {n} |")

    # The column headers are labelled "UKT 3".."UKT 8" but sit at positions 1..6,
    # so a model that reads the label's number as a position lands two columns off.
    offsets: Counter = Counter()
    label_as_index = Counter()
    for rec in wrong:
        item = ITEMS[rec["id"]]
        parsed = parse_table(item["context_markdown"], item["row"])
        got = extract_amounts(rec["response"])
        if not parsed or not got:
            offsets["unparsable"] += 1
            continue
        _, cells = parsed
        values = {i: next(iter(extract_amounts(c)))
                  for i, c in enumerate(cells) if extract_amounts(c)}
        gold_idx = next((i for i, v in values.items()
                         if v == int(item["gold_value"])), None)
        answered = [i for i, v in values.items() if v in got]
        if gold_idx is None or not answered:
            offsets["other"] += 1
            continue
        offsets[answered[0] - gold_idx] += 1
        m = re.search(r"(\d+)", item["column"])
        if m:
            label_as_index["matches" if int(m.group(1)) == answered[0]
                           else "does not match"] += 1

    out += ["", "## Column offset of the wrong answer", "",
            "Offset = position answered minus position of the correct cell.", "",
            "| Offset | n |", "|---|---|"]
    for key, n in sorted(offsets.items(), key=lambda kv: str(kv[0])):
        out.append(f"| {key} | {n} |")

    matched = label_as_index["matches"]
    total_lbl = sum(label_as_index.values())
    out += ["", "## Label-number-as-position hypothesis", "",
            "The wrong cell sits at exactly the position named by the number in the "
            "column label (e.g. \"UKT 5\" read as position 5, though it sits at "
            f"position 3): **{matched} of {total_lbl}** classifiable failures.", ""]

    by_doc: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for rid, rec in seen.items():
        doc = ITEMS[rid]["doc"]
        by_doc[doc][1] += 1
        if not score_record(rec):
            by_doc[doc][0] += 1
    out += ["", "## Failures by source table", "",
            "| Table | Columns | Wrong | Items |", "|---|---|---|---|"]
    width = {"ukt": "6 (wide)", "ipi": "2 (narrow)"}
    for doc, (bad, total) in sorted(by_doc.items()):
        out.append(f"| {doc.upper()} | {width.get(doc, '?')} | {bad} | {total} |")

    out += ["", "## Value repetition in the source tables", ""]
    for doc in sorted({i["doc"] for i in ITEMS.values()}):
        sample = next(i for i in ITEMS.values() if i["doc"] == doc)
        amounts: list[int] = []
        for line in sample["context_markdown"].splitlines():
            if line.strip().startswith("|"):
                for cell in line.strip().strip("|").split("|"):
                    amounts += list(extract_amounts(cell))
        if not amounts:
            continue
        counts = Counter(amounts)
        repeated = sum(n for n in counts.values() if n > 1)
        out.append(f"- **{doc.upper()}**: {len(amounts)} numeric cells, "
                   f"{repeated} ({repeated / len(amounts):.0%}) share their value "
                   f"with another cell in the same table")

    out += cross_encoding_section(args.model, 'llama-3.3-70b-versatile')

    text = "\n".join(out) + "\n"
    (ROOT / "results" / "summary_errors.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
