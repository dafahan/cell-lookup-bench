# Cell-Lookup Micro-Benchmark — Results

## Exact Match per condition

| Model | Condition | n | Lenient EM | 95% CI | Strict EM |
| --- | --- | --- | --- | --- | --- |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c1_markdown | 48 | 42/48 = 87.5% | [75.3%, 94.1%] | 85.4% |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c2_verbalized | 48 | 48/48 = 100.0% | [92.6%, 100.0%] | 70.8% |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c6_verbalized_oracle | 48 | 48/48 = 100.0% | [92.6%, 100.0%] | 100.0% |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c1_markdown | 48 | 44/48 = 91.7% | [80.4%, 96.7%] | 91.7% |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c2_verbalized | 48 | 34/48 = 70.8% | [56.8%, 81.8%] | 70.8% |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c6_verbalized_oracle | 48 | 40/48 = 83.3% | [70.4%, 91.3%] | 83.3% |

## McNemar exact (paired, lenient EM) — within model

| Model | Pair | b (A✓B✗) | c (A✗B✓) | p-value |
| --- | --- | --- | --- | --- |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c1_markdown vs c2_verbalized | 0 | 6 | 0.0312 **(sig.)** |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c1_markdown vs c6_verbalized_oracle | 0 | 6 | 0.0312 **(sig.)** |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c1_markdown vs c2_verbalized | 10 | 0 | 0.0020 **(sig.)** |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c1_markdown vs c6_verbalized_oracle | 4 | 0 | 0.1250 |

## Equalizer tests (cross-model, paired per question)

| Test | A | B | A acc | B acc | b | c | p-value |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Cost & latency (fresh calls only; cached reruns excluded from latency)

| Model | Condition | mean latency (s) | tokens in/out | est. USD per 1000 queries |
| --- | --- | --- | --- | --- |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c1_markdown | 2.13 | 51015/1479 |  |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c2_verbalized | 4.85 | 113207/3632 |  |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | c6_verbalized_oracle | 4.50 | 115511/3369 |  |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c1_markdown | 3.06 | 51015/562 |  |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c2_verbalized | 3.14 | 113207/562 |  |
| meta-llama/Meta-Llama-3.1-8B-Instruct | c6_verbalized_oracle | 2.92 | 115511/562 |  |

## Failures (lenient) — for qualitative error analysis

### meta-llama/Llama-3.3-70B-Instruct-Turbo — c1_markdown (6 failures)
- `a02` gold=Sosiologi → 'JAWABAN: 1.498.000'
- `a04` gold=Ilmu Hukum → 'JAWABAN: 7.300.000'
- `a06` gold=Teknik Sipil → 'JAWABAN: 1.781.000'
- `a10` gold=Agroteknologi → 'JAWABAN: 1.349.000'
- `a14` gold=Ekonomi Pembangunan → 'JAWABAN: 2.073.000'
- `a16` gold=Ilmu Komunikasi → 'JAWABAN: 8.322.000'

### meta-llama/Llama-3.3-70B-Instruct-Turbo — c2_verbalized (0 failures)

### meta-llama/Llama-3.3-70B-Instruct-Turbo — c6_verbalized_oracle (0 failures)

### meta-llama/Meta-Llama-3.1-8B-Instruct — c1_markdown (4 failures)
- `a02` gold=Sosiologi → 'JAWABAN: Ekonomi Pembangunan'
- `a07` gold=1.930.000 → 'JAWABAN: 3.760.000'
- `a10` gold=Agroteknologi → 'JAWABAN: Akuntansi'
- `a14` gold=Ekonomi Pembangunan → 'JAWABAN: Teknik Sipil'

### meta-llama/Meta-Llama-3.1-8B-Instruct — c2_verbalized (14 failures)
- `m01` gold=11.306.000 → 'JAWABAN: 2.915.000'
- `m02` gold=12.451.000 → 'JAWABAN: 20.842.000'
- `m04` gold=11.985.000 → 'JAWABAN: 20.376.000'
- `m10` gold=12.893.000 → 'JAWABAN: 21.284.000'
- `m13` gold=13.122.000 → 'JAWABAN: 4.731.000'
- `m15` gold=15.624.000 → 'JAWABAN: 24.015.000'
- `a02` gold=Sosiologi → 'JAWABAN: Ilmu Hukum'
- `a03` gold=1.200.000 → 'JAWABAN: 1.349.000'
- `a07` gold=1.930.000 → 'JAWABAN: 3.760.000'
- `a09` gold=7.449.000 → 'JAWABAN: 8.033.000'
- `a10` gold=Agroteknologi → 'JAWABAN: Akuntansi'
- `a12` gold=Agroteknologi → 'JAWABAN: Akuntansi'
- `a14` gold=Ekonomi Pembangunan → 'JAWABAN: Ilmu Hukum'
- `a16` gold=Ilmu Komunikasi → 'JAWABAN: 7.706.000'

### meta-llama/Meta-Llama-3.1-8B-Instruct — c6_verbalized_oracle (8 failures)
- `a02` gold=Sosiologi → 'JAWABAN: Ilmu Hukum'
- `a03` gold=1.200.000 → 'JAWABAN: 1.349.000'
- `a07` gold=1.930.000 → 'JAWABAN: 3.760.000'
- `a09` gold=7.449.000 → 'JAWABAN: 8.033.000'
- `a10` gold=Agroteknologi → 'JAWABAN: Akuntansi'
- `a12` gold=Agroteknologi → 'JAWABAN: Akuntansi'
- `a14` gold=Ekonomi Pembangunan → 'JAWABAN: Ilmu Hukum'
- `a16` gold=Ilmu Komunikasi → 'JAWABAN: 7.706.000'
