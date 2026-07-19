# Table format across families (lookup set, n=60)

Exact match per representation. CI = Wilson 95%.

| Family | Scale | Markdown | Verbalized | CSV | HTML | Md+CoT |
|---|---|---|---|---|---|---|
| Llama 3 | small | 75% [63%,84%] | 100% [94%,100%] | 67% [54%,77%] | 75% [63%,84%] | 90% [80%,95%] |
| Llama 3 | large | 100% [94%,100%] | 100% [94%,100%] | 87% [76%,93%] | 90% [80%,95%] | 100% [94%,100%] |
| Qwen2.5 | small | 93% [84%,97%] | 97% [89%,99%] | 77% [65%,86%] | 87% [76%,93%] | 98% [91%,100%] |
| Qwen2.5 | large | 100% [94%,100%] | 100% [94%,100%] | 98% [91%,100%] | 98% [91%,100%] | 98% [91%,100%] |
| Qwen3.5 | small | 87% [76%,93%] | 88% [78%,94%] | 70% [57%,80%] | 82% [70%,89%] | 98% [91%,100%] |
| Qwen3.5 | large | 100% [94%,100%] | 100% [94%,100%] | 95% [86%,98%] | 98% [91%,100%] | 100% [94%,100%] |
| Mistral | small | 88% [78%,94%] | 100% [94%,100%] | 68% [56%,79%] | 77% [65%,86%] | 85% [74%,92%] |
| Mistral | large | 95% [86%,98%] | 100% [94%,100%] | 83% [72%,91%] | 80% [68%,88%] | 98% [91%,100%] |
| Gemma 3 | small | 98% [91%,100%] | 100% [94%,100%] | 95% [86%,98%] | 97% [89%,99%] | 98% [91%,100%] |
| Gemma 3 | large | 93% [84%,97%] | 100% [94%,100%] | 93% [84%,97%] | 92% [82%,96%] | 95% [86%,98%] |

## Paired tests against markdown (McNemar exact)

b = markdown correct & alternative wrong; c = the reverse.

| Family | Scale | Comparison | b | c | p | verdict |
|---|---|---|---|---|---|---|
| Llama 3 | small | md vs Verbalized | 0 | 15 | 0.0001 | Verbalized better |
| Llama 3 | small | md vs CSV | 5 | 0 | 0.0625 | n.s. |
| Llama 3 | small | md vs HTML | 0 | 0 | 1.0000 | n.s. |
| Llama 3 | small | md vs Md+CoT | 0 | 9 | 0.0039 | Md+CoT better |
| Llama 3 | large | md vs Verbalized | 0 | 0 | 1.0000 | n.s. |
| Llama 3 | large | md vs CSV | 8 | 0 | 0.0078 | markdown better |
| Llama 3 | large | md vs HTML | 6 | 0 | 0.0312 | markdown better |
| Llama 3 | large | md vs Md+CoT | 0 | 0 | 1.0000 | n.s. |
| Qwen2.5 | small | md vs Verbalized | 1 | 3 | 0.6250 | n.s. |
| Qwen2.5 | small | md vs CSV | 10 | 0 | 0.0020 | markdown better |
| Qwen2.5 | small | md vs HTML | 5 | 1 | 0.2188 | n.s. |
| Qwen2.5 | small | md vs Md+CoT | 0 | 3 | 0.2500 | n.s. |
| Qwen2.5 | large | md vs Verbalized | 0 | 0 | 1.0000 | n.s. |
| Qwen2.5 | large | md vs CSV | 1 | 0 | 1.0000 | n.s. |
| Qwen2.5 | large | md vs HTML | 1 | 0 | 1.0000 | n.s. |
| Qwen2.5 | large | md vs Md+CoT | 1 | 0 | 1.0000 | n.s. |
| Qwen3.5 | small | md vs Verbalized | 5 | 6 | 1.0000 | n.s. |
| Qwen3.5 | small | md vs CSV | 13 | 3 | 0.0213 | markdown better |
| Qwen3.5 | small | md vs HTML | 7 | 4 | 0.5488 | n.s. |
| Qwen3.5 | small | md vs Md+CoT | 1 | 8 | 0.0391 | Md+CoT better |
| Qwen3.5 | large | md vs Verbalized | 0 | 0 | 1.0000 | n.s. |
| Qwen3.5 | large | md vs CSV | 3 | 0 | 0.2500 | n.s. |
| Qwen3.5 | large | md vs HTML | 1 | 0 | 1.0000 | n.s. |
| Qwen3.5 | large | md vs Md+CoT | 0 | 0 | 1.0000 | n.s. |
| Mistral | small | md vs Verbalized | 0 | 7 | 0.0156 | Verbalized better |
| Mistral | small | md vs CSV | 12 | 0 | 0.0005 | markdown better |
| Mistral | small | md vs HTML | 7 | 0 | 0.0156 | markdown better |
| Mistral | small | md vs Md+CoT | 4 | 2 | 0.6875 | n.s. |
| Mistral | large | md vs Verbalized | 0 | 3 | 0.2500 | n.s. |
| Mistral | large | md vs CSV | 7 | 0 | 0.0156 | markdown better |
| Mistral | large | md vs HTML | 9 | 0 | 0.0039 | markdown better |
| Mistral | large | md vs Md+CoT | 0 | 2 | 0.5000 | n.s. |
| Gemma 3 | small | md vs Verbalized | 0 | 1 | 1.0000 | n.s. |
| Gemma 3 | small | md vs CSV | 2 | 0 | 0.5000 | n.s. |
| Gemma 3 | small | md vs HTML | 1 | 0 | 1.0000 | n.s. |
| Gemma 3 | small | md vs Md+CoT | 0 | 0 | 1.0000 | n.s. |
| Gemma 3 | large | md vs Verbalized | 0 | 4 | 0.1250 | n.s. |
| Gemma 3 | large | md vs CSV | 2 | 2 | 1.0000 | n.s. |
| Gemma 3 | large | md vs HTML | 1 | 0 | 1.0000 | n.s. |
| Gemma 3 | large | md vs Md+CoT | 0 | 1 | 1.0000 | n.s. |
