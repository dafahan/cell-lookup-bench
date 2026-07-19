"""Build the CONTROL dataset that disentangles the two competing accounts of the
small-model cell-lookup failure.

The observational data confound them: the table that fails (UKT) has both offset
column labels ("UKT 3".."UKT 8" sitting at positions 1..6) and a high density of
repeated values, while the tables that never fail (IPI, wide) have aligned labels
*and* unique values. This dataset crosses the two factors so each can be read off
independently:

  label   aligned  — column j is labelled "Kelompok j"      (number == position)
          offset   — column j is labelled "Kelompok j+2"    (number == position+2)
  values  unique   — every cell in the table distinct
          repeated — ~56% of cells share a value with another cell, matching the
                     repetition density measured on the real UKT tables

Prediction under the label-as-position account: failures concentrate in the two
`offset` cells regardless of repetition. Under the value-repetition account: in
the two `repeated` cells regardless of labelling.

Tables are otherwise identical to the failing real one: six numeric columns, a
study-programme row label, Indonesian rupiah amounts.

Usage:  python src/build_control_dataset.py [--n 48] [--seed 11]
Writes: data/benchmark_control.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from verbalizer import verbalize_tables

ROOT = Path(__file__).resolve().parent.parent

PROGRAMS = [
    "Teknik Sipil", "Teknik Mesin", "Teknik Elektro", "Arsitektur",
    "Agroteknologi", "Peternakan", "Manajemen", "Akuntansi",
    "Ilmu Hukum", "Sosiologi", "Biologi", "Kimia",
]
N_COLS = 6
LABEL_OFFSET = 2  # mirrors the real UKT tables: "UKT 3" sits at position 1


def fmt(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def build_table(rng: random.Random, aligned: bool, unique: bool
                ) -> tuple[list[str], list[str], dict[tuple[str, str], int]]:
    """Return (header labels, markdown lines, {(row, column label): value})."""
    start = 1 if aligned else 1 + LABEL_OFFSET
    labels = [f"Kelompok {start + j}" for j in range(N_COLS)]

    if unique:
        pool = rng.sample(range(2_000, 9_999), len(PROGRAMS) * N_COLS)
        values = [[p * 1_000 for p in pool[i * N_COLS:(i + 1) * N_COLS]]
                  for i in range(len(PROGRAMS))]
    else:
        # ~56% of cells repeat: draw from a small pool so collisions are frequent,
        # matching the density measured on the real UKT tables.
        pool = [p * 1_000 for p in rng.sample(range(2_000, 9_999), 14)]
        values = [[rng.choice(pool) for _ in range(N_COLS)] for _ in PROGRAMS]

    lines = ["| Program Studi | " + " | ".join(labels) + " |",
             "|---" * (N_COLS + 1) + "|"]
    gold: dict[tuple[str, str], int] = {}
    for row, cells in zip(PROGRAMS, values):
        lines.append("| " + row + " | " + " | ".join(fmt(v) for v in cells) + " |")
        for label, value in zip(labels, cells):
            gold[(row, label)] = value
    return labels, lines, gold


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=48, help="items per cell of the 2x2")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    items: list[dict] = []
    for aligned in (True, False):
        for unique in (True, False):
            # one seed per cell keeps the four tables independent but reproducible
            rng = random.Random(args.seed + 2 * int(aligned) + int(unique))
            labels, lines, gold = build_table(rng, aligned, unique)
            heading = ("# SIMULASI TARIF KONTROL UNIVERSITAS LAMPUNG\n\n"
                       "## TARIF PER KELOMPOK\n\n")
            table_md = "\n".join(lines)
            context_md = heading + table_md + "\n"
            context_vb = heading + verbalize_tables(table_md, False) + "\n"

            cond = f"{'aligned' if aligned else 'offset'}_{'unique' if unique else 'repeated'}"
            keys = list(gold)
            rng.shuffle(keys)
            for k, (row, label) in enumerate(keys[:args.n], start=1):
                items.append({
                    "id": f"{'a' if aligned else 'o'}{'u' if unique else 'r'}{k:02d}",
                    "doc": f"control_{cond}",
                    "type": cond,
                    "label_alignment": "aligned" if aligned else "offset",
                    "value_pattern": "unique" if unique else "repeated",
                    "n_cols": str(N_COLS),
                    "col_index": str(labels.index(label) + 1),
                    "column_label_number": label.split()[-1],
                    "row": row,
                    "column": label,
                    "question": (f"Berapa tarif {label} untuk program studi {row} "
                                 f"di Universitas Lampung?"),
                    "gold_raw": fmt(gold[(row, label)]),
                    "gold_value": str(gold[(row, label)]),
                    "context_markdown": context_md,
                    "context_verbalized": context_vb,
                })

    out = {"meta": {"n": len(items), "seed": args.seed,
                    "note": "2x2 control: label alignment x value repetition, "
                            f"n={args.n} per cell, {N_COLS} numeric columns"},
           "items": items}
    path = ROOT / "data" / "benchmark_control.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    print(f"wrote {path} ({len(items)} items)")
    print(Counter(i["type"] for i in items))


if __name__ == "__main__":
    main()
