"""Build the cell-lookup benchmark dataset from the gold tariff documents.

For every data cell in every markdown table we generate a candidate question
using the same Indonesian phrasing as the parent RAGAS evaluation set. A
stratified sample (fixed seed) of n=60 is drawn, spread across tables and
columns. Each item carries two gold contexts with identical information:

  context_markdown   — heading hierarchy + the intact table (condition c1)
  context_verbalized — heading hierarchy + per-cell fact sentences (condition c2)

Usage:  python src/build_dataset.py [--n 60] [--seed 42] [--review]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path

from verbalizer import is_table_line, split_cells, is_separator_row, verbalize_block

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "data" / "gold"
OUT = ROOT / "data" / "benchmark.json"

DOCS = {
    "ukt": GOLD / "SK-2661-Tarif-UKT-2025-2026.md",
    "ipi": GOLD / "SK-2662-Tarif-IPI-2025-2026.md",
}

# Landmark cells that must be included (tricky formatting: bold markup, Rp prefix,
# and the highest-value outlier). (doc, row_label, col_header)
FORCED = [
    ("ukt", "Pendidikan Dokter", "UKT 8"),          # **17.050.000** bold cell
    ("ipi", "Pendidikan Dokter (Ilmu Kedokteran)", "IPI 1"),  # **Rp 190.000.000**
    ("ipi", "Farmasi", "IPI 2"),                     # mixed bold/plain row
    ("ukt", "Teknik Sipil (FT)", "UKT 5"),           # D3 row, disambiguation needed
]


@dataclass
class Cell:
    doc: str
    title: str          # h1 line
    section: str        # h2 line
    faculty: str | None  # h3 line (None for tables directly under h2)
    table: list[str]    # verbatim markdown table block
    row_label: str
    col_header: str
    value_raw: str


def normalize_amount(raw: str) -> str:
    """'**Rp 17.050.000**' -> '17050000' (digits only)."""
    return "".join(ch for ch in raw if ch.isdigit())


def parse_cells(doc_id: str, path: Path) -> list[Cell]:
    lines = path.read_text(encoding="utf-8").split("\n")
    title, section, faculty = "", "", None
    cells: list[Cell] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# ") and not title:
            title = line.strip()
        elif line.startswith("### "):
            faculty = line.strip()
        elif line.startswith("## "):
            section = line.strip()
            faculty = None
        elif is_table_line(line):
            start = i
            while i < len(lines) and is_table_line(lines[i]):
                i += 1
            block = lines[start:i]
            if len(block) >= 3 and is_separator_row(block[1]):
                header = split_cells(block[0])
                for row in block[2:]:
                    rc = split_cells(row)
                    if not rc or rc[0] == "":
                        continue
                    for j in range(1, min(len(rc), len(header))):
                        if header[j] == "" or rc[j] == "":
                            continue
                        cells.append(Cell(doc_id, title, section, faculty,
                                          block, rc[0], header[j], rc[j]))
            continue
        i += 1
    return cells


def make_question(c: Cell) -> str:
    if c.doc == "ukt":
        k = c.col_header.replace("UKT", "").strip()
        level = " program Diploma III (D3)" if "DIPLOMA" in c.section.upper() else ""
        return (f"Berapa besaran UKT kelompok {k} untuk program studi {c.row_label}"
                f"{level} di Universitas Lampung tahun akademik 2025/2026?")
    n = c.col_header.replace("IPI", "").strip()
    return (f"Berapa besaran IPI {n} untuk program studi {c.row_label} "
            f"jalur Seleksi Mandiri di Universitas Lampung tahun akademik 2025/2026?")


def table_to_csv(block: list[str]) -> str:
    """Markdown table -> CSV (header + data rows; separator row dropped)."""
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    for i, row in enumerate(block):
        if i == 1 and is_separator_row(row):
            continue
        w.writerow(split_cells(row))
    return buf.getvalue().strip()


def table_to_html(block: list[str]) -> str:
    """Markdown table -> minimal HTML table."""
    header = split_cells(block[0])
    rows = [split_cells(r) for r in block[2:]]
    parts = ["<table>", "  <thead>",
             "    <tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr>",
             "  </thead>", "  <tbody>"]
    for r in rows:
        parts.append("    <tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    parts += ["  </tbody>", "</table>"]
    return "\n".join(parts)


def make_contexts(c: Cell) -> dict[str, str]:
    headings = [h for h in (c.title, c.section, c.faculty) if h]
    table_md = "\n".join(c.table)
    facts = verbalize_block(c.table)
    assert facts, f"table not verbalizable for {c.row_label}"

    def ctx(body: str) -> str:
        return "\n\n".join(headings + [body])

    return {
        "context_markdown": ctx(table_md),
        "context_verbalized": ctx("\n".join(facts)),
        "context_hybrid": ctx("\n".join(facts) + "\n\n" + table_md),
        "context_csv": ctx(table_to_csv(c.table)),
        "context_html": ctx(table_to_html(c.table)),
    }


def table_key(c: Cell) -> tuple:
    return (c.doc, c.section, c.faculty)


def stratified_sample(cells: list[Cell], n: int, seed: int) -> list[Cell]:
    rng = random.Random(seed)
    forced, pool = [], []
    forced_keys = set(FORCED)
    for c in cells:
        if (c.doc, c.row_label, c.col_header) in forced_keys:
            forced.append(c)
        else:
            pool.append(c)

    # Round-robin across tables so every table contributes before any repeats.
    groups: dict[tuple, list[Cell]] = {}
    for c in pool:
        groups.setdefault(table_key(c), []).append(c)
    for g in groups.values():
        rng.shuffle(g)
    order = sorted(groups.keys(), key=str)

    picked = list(forced)
    seen_qs = {make_question(c) for c in picked}
    while len(picked) < n and any(groups[k] for k in order):
        for k in order:
            if len(picked) >= n:
                break
            if groups[k]:
                c = groups[k].pop()
                q = make_question(c)
                if q in seen_qs:  # duplicate row labels across tables
                    continue
                seen_qs.add(q)
                picked.append(c)
    return picked[:n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--review", action="store_true", help="print Q/A pairs for manual review")
    args = ap.parse_args()

    all_cells: list[Cell] = []
    shas = {}
    for doc_id, path in DOCS.items():
        all_cells.extend(parse_cells(doc_id, path))
        shas[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"candidate cells: {len(all_cells)} "
          f"(ukt={sum(c.doc == 'ukt' for c in all_cells)}, "
          f"ipi={sum(c.doc == 'ipi' for c in all_cells)})")

    sample = stratified_sample(all_cells, args.n, args.seed)
    items = []
    for idx, c in enumerate(sample, 1):
        items.append({
            "id": f"q{idx:02d}",
            "doc": c.doc,
            "section": c.section,
            "faculty": c.faculty,
            "row": c.row_label,
            "column": c.col_header,
            "question": make_question(c),
            "gold_raw": c.value_raw,
            "gold_value": normalize_amount(c.value_raw),
            **make_contexts(c),
        })

    payload = {
        "meta": {
            "n": len(items),
            "seed": args.seed,
            "gold_sha256": shas,
            "question_style": "mirrors parent RAGAS eval_dataset.json table_lookup items",
        },
        "items": items,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    by_doc = {d: sum(i["doc"] == d for i in items) for d in DOCS}
    by_col: dict[str, int] = {}
    for i in items:
        by_col[i["column"]] = by_col.get(i["column"], 0) + 1
    print(f"wrote {OUT} n={len(items)} by_doc={by_doc} by_col={dict(sorted(by_col.items()))}")

    if args.review:
        for i in items:
            print(f"{i['id']} [{i['doc']}/{i['column']}] {i['question']}\n"
                  f"     -> {i['gold_raw']} (norm={i['gold_value']})")


if __name__ == "__main__":
    main()
