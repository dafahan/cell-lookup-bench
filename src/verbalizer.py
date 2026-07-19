"""Faithful Python port of the production table verbalizer.

Source of truth: unila-ai backend/pkg/chunk/table.go (VerbalizeTables).
The sentence template, header guards, and cell-splitting rules are replicated
exactly so that the `c2_verbalized` condition tests the *production* technique,
including its quirks (e.g. `**Rp 190.000.000**` bold markup is passed through
verbatim, just like in the deployed system).
"""

from __future__ import annotations


def is_table_line(line: str) -> bool:
    return line.strip().startswith("|")


def split_cells(row: str) -> list[str]:
    row = row.strip()
    row = row.removeprefix("|")
    row = row.removesuffix("|")
    return [p.strip() for p in row.split("|")]


def is_separator_row(row: str) -> bool:
    has_dash = False
    for ch in row.strip():
        if ch == "-":
            has_dash = True
        elif ch not in (":", "|", " ", "\t"):
            return False
    return has_dash


def verbalize_block(block: list[str]) -> list[str] | None:
    """One markdown table -> fact sentences, or None if not verbalizable."""
    if len(block) < 3:
        return None
    header = split_cells(block[0])
    if not is_separator_row(block[1]) or len(header) < 2 or header[0] == "":
        return None

    facts: list[str] = []
    for row in block[2:]:
        cells = split_cells(row)
        if not cells or cells[0] == "":
            continue
        subject = cells[0]
        for j in range(1, min(len(cells), len(header))):
            col, val = header[j], cells[j]
            if col == "" or val == "":
                continue
            facts.append(f"Untuk {header[0]} {subject}, {col} adalah {val}.")
    return facts or None


def verbalize_tables(md: str, keep_table: bool) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not is_table_line(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        start = i
        while i < len(lines) and is_table_line(lines[i]):
            i += 1
        block = lines[start:i]
        facts = verbalize_block(block)
        if facts is not None:
            out.append("")
            out.extend(facts)
            if keep_table:
                out.append("")
                out.extend(block)
            out.append("")
        else:
            out.extend(block)
    return "\n".join(out)
