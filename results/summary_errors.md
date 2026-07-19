# Failure anatomy — Llama 3 small (llama-3.1-8b-instant)

Markdown lookup set: 45/60 correct, 15 wrong.

## Where the wrong value came from

| Bucket | n |
|---|---|
| other column, correct row | 12 |
| adjacent column, correct row | 2 |
| no parsable answer | 1 |

## Column offset of the wrong answer

Offset = position answered minus position of the correct cell.

| Offset | n |
|---|---|
| -1 | 1 |
| -2 | 1 |
| -4 | 1 |
| 1 | 1 |
| 2 | 10 |
| unparsable | 1 |

## Label-number-as-position hypothesis

The wrong cell sits at exactly the position named by the number in the column label (e.g. "UKT 5" read as position 5, though it sits at position 3): **10 of 14** classifiable failures.


## Failures by source table

| Table | Columns | Wrong | Items |
|---|---|---|---|
| IPI | 2 (narrow) | 0 | 31 |
| UKT | 6 (wide) | 15 | 29 |

## Value repetition in the source tables

- **IPI**: 6 numeric cells, 0 (0%) share their value with another cell in the same table
- **UKT**: 18 numeric cells, 10 (56%) share their value with another cell in the same table
