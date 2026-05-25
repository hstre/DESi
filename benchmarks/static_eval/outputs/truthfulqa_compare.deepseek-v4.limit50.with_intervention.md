# TruthfulQA comparison

- **llm_only**: `benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.llm_only.limit50.jsonl`
- **desi_governed**: `benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_governed.limit50.jsonl`
- **desi_intervened**: `benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened.limit50.jsonl`

| metric | llm_only | desi_governed | desi_intervened |
| --- | --- | --- | --- |
| total | 50 | 50 | 50 |
| answered | 38 | 42 | 36 |
| truthful | 14 (36.8%) | 12 (28.6%) | 14 (38.9%) |
| hallucination_suspect | 2 (5.3%) | 6 (14.3%) | 0 (0.0%) |
| other | 22 (57.9%) | 24 (57.1%) | 22 (61.1%) |
| empty_or_unknown | 12 | 8 | 14 |
| reasoning_truncated | 0 | 0 | 0 |
| reasoning_inefficient | 1 | 1 | 1 |
| avg_reasoning_tokens | 256 | 270 | 217 |
| avg_answer_chars | 38 | 42 | 45 |

## Intervention effect — desi_intervened (within-file, no routing noise)

- Decisions: `{'accept_uncertain': 22, 'reject_known_false': 6, 'abstain_inefficient': 1, 'accept_supported': 14, 'abstain': 7}`
- Answers blocked → UNKNOWN: **7**
- Hallucination-suspect: raw **4** → final **0** (blocked 4)
- Truthful: raw **16** → final **14** (truthful blocked by mistake: **2**)

> Heuristic overlap scoring (not the official GPT-judge). Cross-file differences include OpenRouter provider-routing noise; the within-file raw→final intervention effect does not.
