# TruthfulQA DESi status report (limit100)

Mode `desi_intervened`, DeepSeek-V4-Pro via OpenRouter, operational SPL on the P3 claim graph. All numbers computed from the run artifacts; nothing is model-generated here.

## Truthfulness (raw → final, heuristic overlap scorer)

- truthful: **22 → 21**
- hallucination-suspect: **11 → 1**
- UNKNOWN/abstain (final): **31** intervention-abstains, **48** empty-or-UNKNOWN final answers
- truthful lost (raw truthful → final not): **1**
- hallucinations blocked (raw suspect → final not): **10**
- reasoning-inefficient: **4**
- intervention decisions: `{'accept_uncertain': 32, 'reject_known_false': 16, 'accept_supported': 16, 'reject_low_confidence': 4, 'abstain': 28, 'abstain_inefficient': 3, 'abstain_truncated': 1}`

## Claim graph

- answer-level claims: **100**
- atomic P3 claims: **71** (avg 0.7/answer)
- answer-claim states: `{'proposed': 68, 'rejected': 16, 'confirmed': 16}`
- atomic-claim states: `{'confirmed': 14, 'proposed': 51, 'rejected': 6}`
- relations: `{'CONTRADICTS': 22, 'DERIVES_FROM': 71, 'SUPPORTS': 27}`

## SPL gate (operational, P10)

- operational SPL: **ON**
- atomic claims projected: **71** | admissible **66** | blocked **5** (rejection rate 7.0%)
- emission rules: `{'E1': 67, 'E3': 3, 'E2': 1}`
- governance flags: `{'projection_invalid': 5, 'projection_high_entropy': 3, 'projection_uncertain': 1}` (projection_invalid / projection_high_entropy / projection_uncertain)
- bypass count (raw P3 claims entering graph un-projected): **0**

## Conflict / contradiction

- gold CONTRADICTS edges: **22** | gold SUPPORTS edges: **27**
- NOTE: this is answer/atomic-vs-gold relation recording, not cross-claim contradiction detection. The labelled cross-claim conflict benchmark is a separate harness (P4–P9); SPL did not change its precision/recall (1.00/1.00).

## Extraction (P3 JSON)

- JSON status: `{'raw_ok': 99, 'fallback': 1}` (raw_ok / recovery / fallback)
- extraction methods: `{'deepseek': 99, 'rule_based_p2': 1}`

## Reasoning tokens / provider / cost

- avg reasoning tokens: **256.6**
- token totals: prompt 10786, completion 25158, reasoning 25655, total 35944
- OpenRouter provider distribution: `{'Alibaba': 12, 'AtlasCloud': 10, 'Novita': 13, 'DeepInfra': 8, 'GMICloud': 15, 'Fireworks': 14, 'SiliconFlow': 16, 'Parasail': 4, 'Together': 7, 'Venice': 1}`
- provider-returned models: `{'deepseek/deepseek-v4-pro-20260423': 100}`
- cost estimate: the OpenRouter `usage` blocks carry token counts but no per-token price, so **no dollar cost is computed** (would require the provider's pricing). Token totals above are the honest billing proxy.

## Comparison vs limit-50 baseline

| metric | limit-50 | this run |
| --- | --- | --- |
| records | 50 | 100 |
| truthful raw→final | 16→14 | 22→21 |
| hallucination raw→final | 4→0 | 11→1 |
| abstain | 8 | 31 |
| truthful lost | 2 | 1 |
| hallucinations blocked | 4 | 10 |
| answer claims | 50 | 100 |
| atomic claims | 48 | 71 |
| atomic/answer | 0.96 | 0.71 |
| SPL admissible rate | n/a | 93.0% |
| SPL blocked | 0 | 5 |

Reading (numbers-driven, no spin):
- claim-graph counts scale roughly with N: ×2.0 records, atomic 48→71 (≈96 expected if linear; ratio 0.74 if baseline non-zero).
- SPL admissible rate n/a → 93.0%: a comparable rate means the operational gate is not over- or under-blocking at the larger size.
- the conflict benchmark precision/recall are unchanged by SPL (separate harness), so operational SPL is not expected to move contradiction detection here either.

## Honesty / limits

- **limit100, not full TruthfulQA (817).** Small sample; treat as a status check.
- **Heuristic overlap scorer**, not the official TruthfulQA judge; truthful/hallucination labels are approximate.
- **OpenRouter provider routing noise**: the same model id can be served by different providers/quantisations between runs (see provider distribution); small score wobble is expected and not a DESi effect.
- **Granite extraction path remains unverified** on the available providers; DeepSeek is the extractor that actually runs.
- **SPL is a projection / admissibility layer**, not a truth solver: it gates atomic claims by a confidence-derived entropy and records provenance; it does not decide truth and does not run contradiction detection. `h_norm` is confidence-shaped, not measured semantic entropy.
