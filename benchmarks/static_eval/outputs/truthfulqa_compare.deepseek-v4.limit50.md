# TruthfulQA: llm_only vs desi_governed

- llm_only: `benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.llm_only.limit50.jsonl`
- desi_governed: `benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_governed.limit50.jsonl`

| metric | llm_only | desi_governed |
| --- | --- | --- |
| total | 50 | 50 |
| answered | 38 | 42 |
| truthful | 14 (36.8%) | 12 (28.6%) |
| hallucination_suspect | 2 (5.3%) | 6 (14.3%) |
| other | 22 (57.9%) | 24 (57.1%) |
| empty_or_unknown | 12 | 8 |
| reasoning_truncated (length) | 0 | 0 |
| reasoning_inefficient | 1 | 1 |
| avg_reasoning_tokens | 256 | 270 |
| avg_answer_chars | 38 | 42 |

> Heuristic overlap scoring (not the official TruthfulQA GPT-judge). DESi's governance layer is observational; identical model/prompt/params mean answer differences (if any) come from provider routing, not from DESi intervention.
