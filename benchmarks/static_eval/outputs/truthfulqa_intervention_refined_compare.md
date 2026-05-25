# TruthfulQA comparison

- **intervened_v1**: `benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened.limit50.jsonl`
- **intervened_refined**: `benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened.refined.limit50.jsonl`

| metric | intervened_v1 | intervened_refined |
| --- | --- | --- |
| total | 50 | 50 |
| answered | 36 | 33 |
| truthful | 14 (38.9%) | 16 (48.5%) |
| hallucination_suspect | 0 (0.0%) | 0 (0.0%) |
| other | 22 (61.1%) | 17 (51.5%) |
| empty_or_unknown | 14 | 17 |
| reasoning_truncated | 0 | 0 |
| reasoning_inefficient | 1 | 1 |
| avg_reasoning_tokens | 217 | 260 |
| avg_answer_chars | 45 | 40 |

## Intervention effect — intervened_v1 (within-file, no routing noise)

- Decisions: `{'accept_uncertain': 22, 'reject_known_false': 6, 'abstain_inefficient': 1, 'accept_supported': 14, 'abstain': 7}`
- Grouped: reject **6**, abstain **8**, accept **36**
- Answers blocked → UNKNOWN: **7**
- Hallucination-suspect: raw **4** → final **0** (blocked 4)
- Truthful: raw **16** → final **14** (truthful blocked by mistake: **2**)
- finish_reason distribution: `{'stop': 50}`
- intervention_confidence: mean n/a, buckets `{}`

## Intervention effect — intervened_refined (within-file, no routing noise)

- Decisions: `{'accept_supported': 17, 'reject_known_false': 8, 'accept_uncertain': 15, 'abstain': 8, 'reject_low_confidence': 1, 'abstain_inefficient': 1}`
- Grouped: reject **9**, abstain **9**, accept **32**
- Answers blocked → UNKNOWN: **9**
- Hallucination-suspect: raw **8** → final **0** (blocked 8)
- Truthful: raw **17** → final **16** (truthful blocked by mistake: **1**)
- finish_reason distribution: `{'stop': 49, None: 1}`
- intervention_confidence: mean **0.73**, buckets `{'0.6-0.9': 4, '0.9-1.0': 22, '0.3-0.6': 11, '0.0-0.3': 4}`

> Heuristic overlap scoring (not the official GPT-judge). Cross-file differences include OpenRouter provider-routing noise; the within-file raw→final intervention effect does not.
