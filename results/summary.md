# Cell-Lookup Micro-Benchmark — Results

## Exact Match per condition

| Model | Condition | n | Lenient EM | 95% CI | Strict EM |
| --- | --- | --- | --- | --- | --- |
| llama-3.1-8b-instant | c1_markdown | 60 | 45/60 = 75.0% | [62.8%, 84.2%] | 75.0% |
| llama-3.1-8b-instant | c2_verbalized | 60 | 60/60 = 100.0% | [94.0%, 100.0%] | 100.0% |
| llama-3.1-8b-instant | c3_csv | 60 | 40/60 = 66.7% | [54.1%, 77.3%] | 66.7% |
| llama-3.1-8b-instant | c4_html | 60 | 45/60 = 75.0% | [62.8%, 84.2%] | 75.0% |
| llama-3.1-8b-instant | c5_markdown_cot | 60 | 54/60 = 90.0% | [79.9%, 95.3%] | 90.0% |
| llama-3.3-70b-versatile | c1_markdown | 60 | 60/60 = 100.0% | [94.0%, 100.0%] | 100.0% |
| llama-3.3-70b-versatile | c2_verbalized | 60 | 60/60 = 100.0% | [94.0%, 100.0%] | 100.0% |
| llama-3.3-70b-versatile | c3_csv | 60 | 52/60 = 86.7% | [75.8%, 93.1%] | 86.7% |
| llama-3.3-70b-versatile | c4_html | 60 | 54/60 = 90.0% | [79.9%, 95.3%] | 90.0% |
| llama-3.3-70b-versatile | c5_markdown_cot | 60 | 60/60 = 100.0% | [94.0%, 100.0%] | 100.0% |

## McNemar exact (paired, lenient EM) — within model

| Model | Pair | b (A✓B✗) | c (A✗B✓) | p-value |
| --- | --- | --- | --- | --- |
| llama-3.1-8b-instant | c1_markdown vs c2_verbalized | 0 | 15 | 0.0001 **(sig.)** |
| llama-3.1-8b-instant | c1_markdown vs c3_csv | 5 | 0 | 0.0625 |
| llama-3.1-8b-instant | c1_markdown vs c4_html | 0 | 0 | 1.0000 |
| llama-3.1-8b-instant | c1_markdown vs c5_markdown_cot | 0 | 9 | 0.0039 **(sig.)** |
| llama-3.3-70b-versatile | c1_markdown vs c2_verbalized | 0 | 0 | 1.0000 |
| llama-3.3-70b-versatile | c1_markdown vs c3_csv | 8 | 0 | 0.0078 **(sig.)** |
| llama-3.3-70b-versatile | c1_markdown vs c4_html | 6 | 0 | 0.0312 **(sig.)** |
| llama-3.3-70b-versatile | c1_markdown vs c5_markdown_cot | 0 | 0 | 1.0000 |

## Equalizer tests (cross-model, paired per question)

| Test | A | B | A acc | B acc | b | c | p-value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gap dasar: 8B markdown vs 70B markdown | llama-3.1-8b-instant/c1_markdown | llama-3.3-70b-versatile/c1_markdown | 75.0% | 100.0% | 0 | 15 | 0.0001 |
| equalizer: 8B verbalized vs 70B markdown | llama-3.1-8b-instant/c2_verbalized | llama-3.3-70b-versatile/c1_markdown | 100.0% | 100.0% | 0 | 0 | 1.0000 |

## Cost & latency (fresh calls only; cached reruns excluded from latency)

| Model | Condition | mean latency (s) | tokens in/out | est. USD per 1000 queries |
| --- | --- | --- | --- | --- |
| llama-3.1-8b-instant | c1_markdown | 0.38 | 22731/806 | $0.020 |
| llama-3.1-8b-instant | c2_verbalized | 0.38 | 35521/973 | $0.031 |
| llama-3.1-8b-instant | c3_csv | 0.44 | 20789/751 | $0.018 |
| llama-3.1-8b-instant | c4_html | 0.45 | 30918/751 | $0.027 |
| llama-3.1-8b-instant | c5_markdown_cot | 1.26 | 25251/15921 | $0.042 |
| llama-3.3-70b-versatile | c1_markdown | 0.25 | 22731/1099 | $0.238 |
| llama-3.3-70b-versatile | c2_verbalized | 0.30 | 35521/2488 | $0.382 |
| llama-3.3-70b-versatile | c3_csv | 0.32 | 20789/1020 | $0.218 |
| llama-3.3-70b-versatile | c4_html | 0.30 | 30918/1075 | $0.318 |
| llama-3.3-70b-versatile | c5_markdown_cot | 0.80 | 25251/11318 | $0.397 |

## Failures (lenient) — for qualitative error analysis

### llama-3.1-8b-instant — c1_markdown (15 failures)
- `q02` gold=4.500.000 → 'JAWABAN: 2.500.000'
- `q13` gold=6.500.000 → 'Maaf, saya tidak dapat menemukan informasi tentang besaran UKT kelompok 7 untuk program studi Teknik Sipil (FT) program Diploma III (D3) di Universitas Lampung '
- `q14` gold=6.000.000 → 'JAWABAN: 9.000.000'
- `q17` gold=6.000.000 → 'JAWABAN: 10.000.000'
- `q30` gold=3.500.000 → 'JAWABAN: 5.500.000'
- `q31` gold=7.500.000 → 'JAWABAN: 10.500.000'
- `q32` gold=5.500.000 → 'JAWABAN: 8.500.000'
- `q34` gold=7.000.000 → 'JAWABAN: 11.000.000'
- `q35` gold=5.000.000 → 'JAWABAN: 7.500.000'
- `q37` gold=7.000.000 → 'JAWABAN: 8.500.000'
- `q46` gold=6.000.000 → 'JAWABAN: 2.000.000'
- `q49` gold=4.000.000 → 'JAWABAN: 7.000.000'
- `q50` gold=7.500.000 → 'JAWABAN: 11.000.000'
- `q52` gold=4.000.000 → 'JAWABAN: 7.000.000'
- `q54` gold=9.000.000 → 'JAWABAN: 7.000.000'

### llama-3.1-8b-instant — c2_verbalized (0 failures)

### llama-3.1-8b-instant — c3_csv (20 failures)
- `q02` gold=4.500.000 → 'JAWABAN: 2.500.000'
- `q13` gold=6.500.000 → 'JAWABAN: 2.500.000'
- `q14` gold=6.000.000 → 'JAWABAN: 9.000.000'
- `q17` gold=6.000.000 → 'JAWABAN: 10.000.000'
- `q18` gold=7.500.000 → 'JAWABAN: 8.500.000'
- `q21` gold=11.000.000 → 'JAWABAN: 13.000.000'
- `q30` gold=3.500.000 → 'JAWABAN: 5.500.000'
- `q31` gold=7.500.000 → 'JAWABAN: 10.500.000'
- `q32` gold=5.500.000 → 'JAWABAN: 8.500.000'
- `q34` gold=7.000.000 → 'JAWABAN: 11.000.000'
- `q35` gold=5.000.000 → 'JAWABAN: 7.500.000'
- `q37` gold=7.000.000 → 'JAWABAN: 10.000.000'
- `q38` gold=11.000.000 → 'JAWABAN: 13.000.000'
- `q46` gold=6.000.000 → 'JAWABAN: 2.000.000'
- `q49` gold=4.000.000 → 'JAWABAN: 7.000.000'
- `q50` gold=7.500.000 → 'JAWABAN: 11.000.000'
- `q51` gold=7.500.000 → 'JAWABAN: 8.500.000'
- `q52` gold=4.000.000 → 'JAWABAN: 7.000.000'
- `q53` gold=2.500.000 → 'JAWABAN: 5.500.000'
- `q54` gold=9.000.000 → 'JAWABAN: 13.000.000'

### llama-3.1-8b-instant — c4_html (15 failures)
- `q02` gold=4.500.000 → 'JAWABAN: 5.500.000'
- `q13` gold=6.500.000 → 'JAWABAN: 2.500.000'
- `q14` gold=6.000.000 → 'JAWABAN: 9.000.000'
- `q17` gold=6.000.000 → 'JAWABAN: 8.000.000'
- `q30` gold=3.500.000 → 'JAWABAN: 5.500.000'
- `q31` gold=7.500.000 → 'JAWABAN: 9.000.000'
- `q32` gold=5.500.000 → 'JAWABAN: 8.500.000'
- `q34` gold=7.000.000 → 'JAWABAN: 11.000.000'
- `q35` gold=5.000.000 → 'JAWABAN: 7.500.000'
- `q37` gold=7.000.000 → 'JAWABAN: 8.500.000'
- `q46` gold=6.000.000 → 'JAWABAN: 4.000.000'
- `q49` gold=4.000.000 → 'JAWABAN: 5.500.000'
- `q50` gold=7.500.000 → 'JAWABAN: 9.000.000'
- `q52` gold=4.000.000 → 'JAWABAN: 7.000.000'
- `q54` gold=9.000.000 → 'JAWABAN: 13.000.000'

### llama-3.1-8b-instant — c5_markdown_cot (6 failures)
- `q13` gold=6.500.000 → 'JAWABAN: 6.000.000'
- `q14` gold=6.000.000 → 'JAWABAN: 9.000.000'
- `q17` gold=6.000.000 → 'JAWABAN: 7.000.000'
- `q30` gold=3.500.000 → 'JAWABAN: 4.000.000'
- `q32` gold=5.500.000 → 'JAWABAN: 8.500.000'
- `q37` gold=7.000.000 → 'JAWABAN: 10.000.000'

### llama-3.3-70b-versatile — c1_markdown (0 failures)

### llama-3.3-70b-versatile — c2_verbalized (0 failures)

### llama-3.3-70b-versatile — c3_csv (8 failures)
- `q02` gold=4.500.000 → 'JAWABAN: 5.500.000'
- `q13` gold=6.500.000 → 'JAWABAN: 7.500.000'
- `q14` gold=6.000.000 → 'JAWABAN: 9.000.000'
- `q30` gold=3.500.000 → 'JAWABAN: 4.500.000'
- `q34` gold=7.000.000 → 'JAWABAN: 11.000.000'
- `q37` gold=7.000.000 → 'JAWABAN: 8.500.000'
- `q50` gold=7.500.000 → 'JAWABAN: 11.000.000'
- `q54` gold=9.000.000 → 'JAWABAN: 11.000.000'

### llama-3.3-70b-versatile — c4_html (6 failures)
- `q13` gold=6.500.000 → 'JAWABAN: 7.500.000'
- `q31` gold=7.500.000 → 'JAWABAN: 9.000.000'
- `q37` gold=7.000.000 → 'JAWABAN: 8.500.000'
- `q46` gold=6.000.000 → 'JAWABAN: 7.000.000'
- `q50` gold=7.500.000 → 'JAWABAN: 11.000.000'
- `q54` gold=9.000.000 → 'JAWABAN: 11.000.000'

### llama-3.3-70b-versatile — c5_markdown_cot (0 failures)
