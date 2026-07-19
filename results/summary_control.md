# Control experiment — label alignment x value repetition

Markdown context, n=48 per cell. CI = Wilson 95%.

## Exact match per cell of the 2x2

| Model | aligned+unique | aligned+repeated | offset+unique | offset+repeated |
|---|---|---|---|---|
| meta-llama/Meta-Llama-3.1-8B-Instruct | 100% [93%,100%] | 96% [86%,99%] | 56% [42%,69%] | 54% [40%,67%] |
| mistralai/Mistral-Nemo-Instruct-2407 | 100% [93%,100%] | 100% [93%,100%] | 100% [93%,100%] | 94% [83%,98%] |
| Qwen/Qwen3.5-9B | 100% [93%,100%] | 100% [93%,100%] | 90% [78%,95%] | 85% [73%,93%] |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | 100% [93%,100%] | 100% [93%,100%] | 81% [68%,90%] | 83% [70%,91%] |

## Marginal effects (markdown)

| Model | aligned | offset | Δ | unique | repeated | Δ |
|---|---|---|---|---|---|---|
| meta-llama/Meta-Llama-3.1-8B-Instruct | 98% [93%,99%] | 55% [45%,65%] | **+43 pp** | 78% [69%,85%] | 75% [65%,83%] | +3 pp |
| mistralai/Mistral-Nemo-Instruct-2407 | 100% [96%,100%] | 97% [91%,99%] | **+3 pp** | 100% [96%,100%] | 97% [91%,99%] | +3 pp |
| Qwen/Qwen3.5-9B | 100% [96%,100%] | 88% [79%,93%] | **+12 pp** | 95% [88%,98%] | 93% [86%,96%] | +2 pp |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | 100% [96%,100%] | 82% [73%,89%] | **+18 pp** | 91% [83%,95%] | 92% [84%,96%] | -1 pp |

## Paired tests (McNemar exact, markdown)

| Model | comparison | b | c | p |
|---|---|---|---|---|
| meta-llama/Meta-Llama-3.1-8B-Instruct | aligned vs offset | 42 | 1 | 0.0000 |
| meta-llama/Meta-Llama-3.1-8B-Instruct | unique vs repeated | 18 | 15 | 0.7283 |
| mistralai/Mistral-Nemo-Instruct-2407 | aligned vs offset | 3 | 0 | 0.2500 |
| mistralai/Mistral-Nemo-Instruct-2407 | unique vs repeated | 3 | 0 | 0.2500 |
| Qwen/Qwen3.5-9B | aligned vs offset | 12 | 0 | 0.0005 |
| Qwen/Qwen3.5-9B | unique vs repeated | 5 | 3 | 0.7266 |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | aligned vs offset | 17 | 0 | 0.0000 |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | unique vs repeated | 6 | 7 | 1.0000 |

## Verbalization as positive control

| Model | markdown | verbalized |
|---|---|---|
| meta-llama/Meta-Llama-3.1-8B-Instruct | 77% [70%,82%] | 97% [93%,99%] |
| mistralai/Mistral-Nemo-Instruct-2407 | 98% [96%,99%] | 99% [97%,100%] |
| Qwen/Qwen3.5-9B | 94% [89%,96%] | 100% [98%,100%] |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | 91% [86%,94%] | 100% [98%,100%] |

## Signature: wrong answer lands on the label-named position

| Model | wrong (offset cells) | of which land on label position |
|---|---|---|
| meta-llama/Meta-Llama-3.1-8B-Instruct | 43 | 19/43 |
| mistralai/Mistral-Nemo-Instruct-2407 | 3 | 0/3 |
| Qwen/Qwen3.5-9B | 12 | 12/12 |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | 17 | 17/17 |
