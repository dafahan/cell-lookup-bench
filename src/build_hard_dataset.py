"""Build the HARD-MODE cell-lookup dataset: synthetic complex tables that probe
the limits of the equalizer claim.

Two table types (deterministic, seed-controlled):

  wide       — flat single-header table with 12 numeric columns (Semester 1..12).
               Every cell value in a table is unique, so any wrong-row or
               wrong-column read is detectable (unlike the conservative main set).
  multilevel — two-level header encoded the way PDF->markdown converters emit it:
               a group header row (repeated span labels), a separator, then a
               sub-header row as the first "body" row. The production verbalizer
               accepts this table but produces AMBIGUOUS facts (two columns share
               the group label) — measuring naive verbalization on complex tables
               is part of the experiment. An oracle verbalization (correct
               group+sub labels) provides the upper bound.

Contexts per item:
  context_markdown           — raw table + headings
  context_verbalized         — production verbalizer output (port of table.go)
  context_verbalized_oracle  — hand-constructed unambiguous facts

Usage: python src/build_hard_dataset.py [--seed 7] [--review]
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from verbalizer import verbalize_tables

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "benchmark_hard.json"

PRODI = [
    "Manajemen", "Akuntansi", "Ekonomi Pembangunan", "Ilmu Hukum", "Agroteknologi",
    "Teknik Sipil", "Teknik Elektro", "Teknik Informatika", "Sosiologi",
    "Ilmu Komunikasi", "Matematika", "Fisika", "Ilmu Komputer", "Biologi", "Farmasi",
]

TITLE = "# SIMULASI TARIF LAYANAN AKADEMIK UNIVERSITAS LAMPUNG 2025/2026"


def fmt(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def build_wide(rng: random.Random) -> tuple[list[str], dict]:
    """15 rows x 12 columns, all cell values unique."""
    cols = [f"Semester {i}" for i in range(1, 13)]
    header = "| Program Studi | " + " | ".join(cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    rows, values = [], {}
    for r, p in enumerate(PRODI):
        cells = []
        for c in range(12):
            v = 1_500_000 + r * 730_000 + c * 145_000 + ((r * 7 + c * 13) % 11) * 1_000
            values[(p, cols[c])] = v
            cells.append(fmt(v))
        rows.append(f"| {p} | " + " | ".join(cells) + " |")
    return [header, sep] + rows, values


def build_agg(rng: random.Random) -> tuple[list[str], dict]:
    """10 rows x 12 columns for aggregation queries. The per-column ranking of
    programs varies (multiplicative permutation mod 11), so max/min answers
    differ across columns and cannot be pattern-guessed."""
    prodi = PRODI[:10]
    cols = [f"Semester {i}" for i in range(1, 13)]
    header = "| Program Studi | " + " | ".join(cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    rows, values = [], {}
    for r, p in enumerate(prodi):
        cells = []
        for c in range(12):
            rank = (r * 7 + c * 5) % 11  # 7 coprime with 11 -> per-column permutation
            v = 1_200_000 + rank * 610_000 + c * 145_000 + ((r * 3 + c) % 9) * 1_000
            values[(p, cols[c])] = v
            cells.append(fmt(v))
        rows.append(f"| {p} | " + " | ".join(cells) + " |")
    return [header, sep] + rows, values


def build_multilevel(rng: random.Random) -> tuple[list[str], dict, list[str], list[str]]:
    """Two-level header: 3 admission tracks x (UKT, IPI) = 6 data columns."""
    groups = ["Jalur SNBP", "Jalur SNBT", "Jalur Mandiri"]
    subs = ["UKT", "IPI"]
    top = "| Program Studi | " + " | ".join(g for g in groups for _ in subs) + " |"
    sep = "|" + "---|" * 7
    subrow = "| | " + " | ".join(subs * len(groups)) + " |"
    rows, values, oracle = [], {}, []
    for r, p in enumerate(PRODI[:12]):
        cells = []
        for gi, g in enumerate(groups):
            for si, s in enumerate(subs):
                v = 2_000_000 + r * 910_000 + gi * 3_170_000 + si * 8_390_000 \
                    + ((r * 5 + gi * 3 + si) % 7) * 1_000
                values[(p, g, s)] = v
                cells.append(fmt(v))
                oracle.append(f"Untuk Program Studi {p}, {s} {g.lower()} adalah {fmt(v)}.")
        rows.append(f"| {p} | " + " | ".join(cells) + " |")
    block = [top, sep, subrow] + rows
    return block, values, oracle, groups


def build_arith(rng: random.Random) -> tuple[list[str], dict, list[str], list[str]]:
    """12 rows x 8 columns, unique values; substrate for column arithmetic
    (sum of a semester range / difference between two semesters). Single header,
    so the production verbalizer produces clean per-cell facts — the difficulty is
    that answering requires *combining* several facts, which fragmentation impedes."""
    prodi = PRODI[:12]
    cols = [f"Semester {i}" for i in range(1, 9)]
    header = "| Program Studi | " + " | ".join(cols) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    rows, values = [], {}
    for r, p in enumerate(prodi):
        cells = []
        for c in range(8):
            v = 2_100_000 + r * 517_000 + c * 311_000 + ((r * 5 + c * 7) % 13) * 1_000
            values[(p, cols[c])] = v
            cells.append(fmt(v))
        rows.append(f"| {p} | " + " | ".join(cells) + " |")
    return [header, sep] + rows, values, cols, prodi


def build_header3(rng: random.Random) -> tuple[list[str], dict, list[str], list[tuple]]:
    """Three-level header: 2 tracks x 2 terms x (UKT, IPI) = 8 data columns, encoded
    as PDF->markdown emits it (top row = level-1, then separator, then two sub-header
    rows as body rows). The production verbalizer sees only the level-1 row, so every
    fact is *four-way* ambiguous (four columns share each track label). The oracle
    verbalization spells out the full track/term/metric path."""
    tracks = ["Jalur SNBP", "Jalur Mandiri"]
    terms = ["Ganjil", "Genap"]
    metrics = ["UKT", "IPI"]
    leaves = [(t, tm, mt) for t in tracks for tm in terms for mt in metrics]  # 8
    top = "| Program Studi | " + " | ".join(t for t in tracks for _ in range(4)) + " |"
    sep = "|" + "---|" * (len(leaves) + 1)
    midrow = "| | " + " | ".join(tm for _ in tracks for tm in terms for _ in metrics) + " |"
    subrow = "| | " + " | ".join(mt for _ in tracks for _ in terms for mt in metrics) + " |"
    rows, values, oracle = [], {}, []
    for r, p in enumerate(PRODI[:12]):
        cells = []
        for (t, tm, mt) in leaves:
            ti, mi, si = tracks.index(t), terms.index(tm), metrics.index(mt)
            v = 3_000_000 + r * 830_000 + ti * 4_130_000 + mi * 1_770_000 \
                + si * 6_310_000 + ((r * 5 + ti * 3 + mi * 2 + si) % 7) * 1_000
            values[(p, t, tm, mt)] = v
            cells.append(fmt(v))
            oracle.append(
                f"Untuk Program Studi {p}, {mt} {t.lower()} semester {tm.lower()} adalah {fmt(v)}.")
        rows.append(f"| {p} | " + " | ".join(cells) + " |")
    block = [top, sep, midrow, subrow] + rows
    return block, values, oracle, leaves


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--review", action="store_true")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    items = []

    # --- wide ---
    wide_block, wide_vals = build_wide(rng)
    heading = f"{TITLE}\n\n## TARIF SPP PROGRAM SARJANA (SIMULASI)"
    table_md = "\n".join(wide_block)
    ctx_md = f"{heading}\n\n{table_md}"
    ctx_vb = f"{heading}\n\n{verbalize_tables(table_md, keep_table=False).strip()}"
    wide_cells = [(p, k) for p in PRODI for k in range(1, 13)]  # 15 x 12 = 180
    qn = 0
    for p, k in rng.sample(wide_cells, 48):
        qn += 1
        v = wide_vals[(p, f"Semester {k}")]
        items.append({
            "id": f"w{qn:02d}", "doc": "hard_wide", "type": "wide",
            "n_cols": 12, "col_index": k,
            "row": p, "column": f"Semester {k}",
            "question": (f"Berapa tarif SPP Semester {k} untuk program studi {p} "
                         f"menurut tabel simulasi tarif layanan akademik 2025/2026?"),
            "gold_raw": fmt(v), "gold_value": str(v),
            "context_markdown": ctx_md,
            "context_verbalized": ctx_vb,
            "context_verbalized_oracle": ctx_vb,  # single-header: prod == oracle
        })

    # --- multilevel ---
    ml_block, ml_vals, ml_oracle, groups = build_multilevel(rng)
    heading2 = f"{TITLE}\n\n## TARIF UKT DAN IPI PER JALUR MASUK (SIMULASI)"
    table_md2 = "\n".join(ml_block)
    ctx_md2 = f"{heading2}\n\n{table_md2}"
    ctx_vb2 = f"{heading2}\n\n{verbalize_tables(table_md2, keep_table=False).strip()}"
    ctx_or2 = f"{heading2}\n\n" + "\n".join(ml_oracle)
    ml_qs = [(p, g, s) for p in PRODI[:12] for g in groups for s in ["UKT", "IPI"]]
    qn = 0
    for p, g, s in rng.sample(ml_qs, 48):
        qn += 1
        v = ml_vals[(p, g, s)]
        items.append({
            "id": f"m{qn:02d}", "doc": "hard_multilevel", "type": "multilevel",
            "n_cols": 6, "col_index": None,
            "row": p, "column": f"{g} / {s}",
            "question": (f"Berapa {s} {g.lower()} untuk program studi {p} "
                         f"menurut tabel simulasi tarif layanan akademik 2025/2026?"),
            "gold_raw": fmt(v), "gold_value": str(v),
            "context_markdown": ctx_md2,
            "context_verbalized": ctx_vb2,
            "context_verbalized_oracle": ctx_or2,
        })

    # --- aggregation (cross-column reasoning; lookup is not enough) ---
    agg_block, agg_vals = build_agg(rng)
    heading3 = f"{TITLE}\n\n## TARIF SPP PER SEMESTER (SIMULASI, PROGRAM TERPILIH)"
    table_md3 = "\n".join(agg_block)
    ctx_md3 = f"{heading3}\n\n{table_md3}"
    ctx_vb3 = f"{heading3}\n\n{verbalize_tables(table_md3, keep_table=False).strip()}"
    agg_prodi = PRODI[:10]
    agg_cols = [f"Semester {i}" for i in range(1, 13)]
    qn = 0
    for col in rng.sample(agg_cols, 12):
        colvals = {p: agg_vals[(p, col)] for p in agg_prodi}
        hi = max(colvals, key=colvals.get)
        lo = min(colvals, key=colvals.get)
        k = col.split()[-1]
        # two numeric-answer questions (highest / lowest value in the column)
        for which, target in [("tertinggi", colvals[hi]), ("terendah", colvals[lo])]:
            qn += 1
            items.append({
                "id": f"a{qn:02d}", "doc": "hard_agg", "type": "aggregation",
                "n_cols": 12, "col_index": int(k),
                "row": "-", "column": col,
                "question": (f"Berapa tarif SPP Semester {k} yang paling {which} "
                             f"di antara semua program studi pada tabel simulasi?"),
                "gold_raw": fmt(target), "gold_value": str(target),
                "context_markdown": ctx_md3,
                "context_verbalized": ctx_vb3,
                "context_verbalized_oracle": ctx_vb3,
            })
        # two name-answer questions (which program is highest / lowest)
        for which, target_name in [("paling tinggi", hi), ("paling rendah", lo)]:
            qn += 1
            items.append({
                "id": f"a{qn:02d}", "doc": "hard_agg", "type": "aggregation",
                "n_cols": 12, "col_index": int(k),
                "row": target_name, "column": col,
                "question": (f"Program studi mana yang tarif SPP Semester {k}-nya "
                             f"{which} pada tabel simulasi?"),
                "gold_raw": target_name, "gold_value": target_name,
                "distractors": [p for p in agg_prodi if p != target_name],
                "context_markdown": ctx_md3,
                "context_verbalized": ctx_vb3,
                "context_verbalized_oracle": ctx_vb3,
            })

    # --- arithmetic (column sum / difference; single header, clean facts, but the
    #     answer requires combining several cells -> verbalization fragments them) ---
    arith_block, arith_vals, arith_cols, arith_prodi = build_arith(rng)
    heading4 = f"{TITLE}\n\n## TARIF SPP PER SEMESTER (SIMULASI, UNTUK PERHITUNGAN)"
    table_md4 = "\n".join(arith_block)
    ctx_md4 = f"{heading4}\n\n{table_md4}"
    ctx_vb4 = f"{heading4}\n\n{verbalize_tables(table_md4, keep_table=False).strip()}"
    qn = 0
    for _ in range(24):  # sum over a contiguous semester range
        p = rng.choice(arith_prodi)
        a = rng.randint(1, 5)
        b = rng.randint(a + 1, min(a + 3, 8))
        total = sum(arith_vals[(p, f"Semester {i}")] for i in range(a, b + 1))
        qn += 1
        items.append({
            "id": f"ar{qn:02d}", "doc": "hard_arith", "type": "arithmetic",
            "n_cols": 8, "col_index": None, "row": p, "column": f"Sem{a}-{b} sum",
            "question": (f"Berapa TOTAL tarif SPP dari Semester {a} sampai Semester {b} "
                         f"untuk program studi {p} menurut tabel simulasi?"),
            "gold_raw": fmt(total), "gold_value": str(total),
            "context_markdown": ctx_md4, "context_verbalized": ctx_vb4,
            "context_verbalized_oracle": ctx_vb4,
        })
    for _ in range(24):  # difference between two semesters
        p = rng.choice(arith_prodi)
        x, y = sorted(rng.sample(range(1, 9), 2), reverse=True)
        diff = arith_vals[(p, f"Semester {x}")] - arith_vals[(p, f"Semester {y}")]
        qn += 1
        items.append({
            "id": f"ar{qn:02d}", "doc": "hard_arith", "type": "arithmetic",
            "n_cols": 8, "col_index": None, "row": p, "column": f"Sem{x}-{y} diff",
            "question": (f"Berapa SELISIH tarif SPP Semester {x} dan Semester {y} "
                         f"untuk program studi {p} menurut tabel simulasi?"),
            "gold_raw": fmt(diff), "gold_value": str(diff),
            "context_markdown": ctx_md4, "context_verbalized": ctx_vb4,
            "context_verbalized_oracle": ctx_vb4,
        })

    # --- header3 (three-level header; production verbalizer is four-way ambiguous) ---
    h3_block, h3_vals, h3_oracle, h3_leaves = build_header3(rng)
    heading5 = f"{TITLE}\n\n## TARIF UKT/IPI PER JALUR DAN SEMESTER (SIMULASI)"
    table_md5 = "\n".join(h3_block)
    ctx_md5 = f"{heading5}\n\n{table_md5}"
    ctx_vb5 = f"{heading5}\n\n{verbalize_tables(table_md5, keep_table=False).strip()}"
    ctx_or5 = f"{heading5}\n\n" + "\n".join(h3_oracle)
    h3_qs = [(p, t, tm, mt) for p in PRODI[:12] for (t, tm, mt) in h3_leaves]
    qn = 0
    for p, t, tm, mt in rng.sample(h3_qs, 48):
        qn += 1
        v = h3_vals[(p, t, tm, mt)]
        items.append({
            "id": f"h{qn:02d}", "doc": "hard_header3", "type": "header3",
            "n_cols": 8, "col_index": None, "row": p, "column": f"{t}/{tm}/{mt}",
            "question": (f"Berapa {mt} {t.lower()} untuk semester {tm.lower()} pada "
                         f"program studi {p} menurut tabel simulasi?"),
            "gold_raw": fmt(v), "gold_value": str(v),
            "context_markdown": ctx_md5, "context_verbalized": ctx_vb5,
            "context_verbalized_oracle": ctx_or5,
        })

    # hybrid context (facts + intact table, matching the deployed S6 config):
    # reconstruct from the shared heading prefix of the markdown and verbalized ctx.
    for it in items:
        md, vb = it["context_markdown"], it["context_verbalized"]
        n = 0
        while n < min(len(md), len(vb)) and md[n] == vb[n]:
            n += 1
        head, table_body, facts_body = md[:n], md[n:], vb[n:]
        it["context_hybrid"] = head + facts_body.rstrip() + "\n\n" + table_body.lstrip()

    payload = {
        "meta": {
            "n": len(items), "seed": args.seed,
            "note": ("synthetic hard-mode tables (n=48/type): wide, multilevel, "
                     "aggregation, arithmetic, header3"),
        },
        "items": items,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    from collections import Counter
    print(f"wrote {OUT} n={len(items)} by_type={Counter(i['type'] for i in items)}")

    if args.review:
        for i in items:
            print(f"{i['id']} [{i['type']}] {i['question']} -> {i['gold_raw']}")
        print("\n--- production verbalizer output on multilevel (first 4 lines) ---")
        print("\n".join(ctx_vb2.splitlines()[4:8]))
        print("--- oracle (first 4 lines) ---")
        print("\n".join(ctx_or2.splitlines()[4:8]))


if __name__ == "__main__":
    main()
