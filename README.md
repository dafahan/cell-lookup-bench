# cell-lookup-bench

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21440722.svg)](https://doi.org/10.5281/zenodo.21440722)
[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)

A retrieval-free benchmark that isolates **why language models return the wrong cell** when reading tables, and measures what repairs it.

Every question is paired with a *gold context* guaranteed to contain the answer, so retrieval contributes nothing by construction and any error is a reading error. Scoring is **deterministic exact match with no LLM judge**, so every number in the accompanying article can be reproduced from the shipped raw responses without spending a cent on API calls.

Companion artifact for: *Does Table Representation Substitute for Model Scale? A Controlled Study of Column-Label Misalignment in Open-Weight Language Models.*

## The headline finding

Column headers such as `UKT 3 | UKT 4 | ... | UKT 8` sit at positions 1 to 6. A model that reads the number inside a column's **name** as that column's **position** lands two columns away. On real tuition tables, 10 of the 14 classifiable failures of Llama 3.1 8B land at exactly that offset.

A 2×2 controlled experiment confirms the cause and rejects the alternative:

| | Misaligned labels | Repeated values |
|---|---|---|
| Llama 3.1 8B | **−43 pp** (p < 0.001) | −3 pp (n.s.) |
| Llama 3.3 70B | **−18 pp** (p < 0.01) | +1 pp (n.s.) |
| Qwen3.5 9B | **−12 pp** (p < 0.001) | −2 pp (n.s.) |
| Mistral Nemo 12B | −3 pp (n.s.) | −3 pp (n.s.) |

Value repetition is not significant in a single model. Large models are affected too, so this is a general defect that scale attenuates rather than removes.

## Reproducing the article's tables

No API keys and no network access are required. The raw responses are in `results/`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python src/score_format.py                    # Table 5  — encodings across families
python src/score_errors.py                    # Table 6  — anatomy of the failures
python src/score_control.py                   # Table 7  — the 2x2 control
python src/score_family.py results/run_*.json # Tables 8, 10, 11 — families and stress
python src/score.py results/run_groq_*.json   # Table 12 — cost and latency
```

Each script prints a Markdown report and writes it to `results/summary_*.md`.

| Script | Produces | Article table |
|---|---|---|
| `score_format.py` | `summary_format.md` | 5 |
| `score_errors.py` | `summary_errors.md` | 6 |
| `score_control.py` | `summary_control.md` | 7 |
| `score_family.py` | `summary_family.md` | 8, 10, 11 |
| `score.py` | `summary.md` | 12 |

## Running new experiments

This *does* need API credentials.

```bash
cp .env.example .env      # then fill in your keys
python src/run_bench.py --provider deepinfra \
    --model "meta-llama/Meta-Llama-3.1-8B-Instruct" \
    --dataset data/benchmark.json \
    --conditions c1_markdown,c2_verbalized \
    --tag myrun --workers 4
```

Responses are cached by prompt hash in `results/cache.json`, so re-runs cost nothing. That cache is deliberately excluded from version control; the committed `run_*.json` files are the authoritative record.

## Layout

```
src/
  run_bench.py             benchmark harness (conditions x questions x model)
  providers.py             Groq / DeepInfra / Together / Ollama clients
  verbalizer.py            table -> per-cell factual sentences
  build_dataset.py         builds the 60-item lookup set from the decrees
  build_hard_dataset.py    builds the five stress structures
  build_control_dataset.py builds the 2x2 control design
  score.py                 exact-match scoring, cost and latency
  score_family.py          cross-family and cross-scale analysis
  score_format.py          encoding comparison
  score_errors.py          failure anatomy
  score_control.py         2x2 control analysis
data/
  benchmark.json           60 cell-lookup items over the real tables
  benchmark_hard.json      240 items, five synthetic stress structures
  benchmark_control.json   192 items, 2x2 control design
  gold/                    Markdown conversions of the two source decrees
results/                   raw responses, one JSON per model per run
figures/                   figure generation and rendered figures
```

## Conditions

| Code | Kind | Context given to the model |
|---|---|---|
| `c1_markdown` | encoding | intact Markdown table |
| `c3_csv` | encoding | CSV |
| `c4_html` | encoding | HTML `<table>` |
| `c2_verbalized` | transformation | one factual sentence per cell |
| `c6_verbalized_oracle` | transformation | verbalization spelling out full header paths |
| `c7_hybrid` | transformation | intact table *and* per-cell sentences |
| `c5_markdown_cot` | prompting | intact Markdown, chain-of-thought instruction |

All seven carry identical information, so any accuracy difference is an effect of representation alone.

## Models

Five open-weight families, each with a smaller and a larger checkpoint: Llama 3 (8B / 70B), Qwen2.5 (7B / 72B), Qwen3.5 (9B / 27B), Mistral (Nemo 12B / Small 24B), Gemma 3 (12B / 27B). Temperature 0 throughout.

Four of the five within-family scale comparisons run on a single provider. Qwen2.5 is the exception, since only Together hosts the 7B checkpoint serverlessly; its accuracy is reported but its cost comparison is not, because that would compare price lists rather than model sizes.

## Scoring

A response must end with a line of the form `JAWABAN: <value>`. Only the span after the final marker is scored. Monetary amounts are normalized so that `Rp 3.000.000`, `3.000.000`, and `3 juta` are equivalent. Paired comparisons use McNemar's exact test; proportions carry Wilson 95% intervals.

## Known caveats

- The stress and control tables are synthetic. This is deliberate: real documents never vary one factor at a time. Prevalence in real documents is measured separately on the two decrees.
- Serving precision on hosted inference is undocumented and may differ between providers.
- Prices in `src/score.py` are list prices captured on 19 July 2026 and will drift.
- The corpus is one document domain, in Indonesian.

## Licence and citation

Code under [MIT](LICENSE). Data and results under [CC BY 4.0](LICENSE-DATA), which also documents the provenance of the source decrees.

Archived on Zenodo with a version-independent DOI that always resolves to the latest release:

```bibtex
@software{haqiqi_cell_lookup_bench,
  author  = {Haqiqi, Dafa Farhan},
  title   = {cell-lookup-bench: a retrieval-free benchmark for table
             cell lookup in open-weight language models},
  year    = {2026},
  doi     = {10.5281/zenodo.21440722},
  url     = {https://doi.org/10.5281/zenodo.21440722}
}
```

To cite a specific release instead, use its own DOI from the Zenodo record. See [CITATION.cff](CITATION.cff) for other formats.
