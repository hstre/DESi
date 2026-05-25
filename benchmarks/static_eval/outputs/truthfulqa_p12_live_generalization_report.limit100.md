# TruthfulQA limit-100 — P12 live generalization run

A REAL new limit-100 run (newly generated answers) under the P12 intervention, compared against the original recorded run and the P12 deterministic replay. The live run's raw answers and providers differ from the original — this tests generalization, and provider/generation noise is present again (unlike the replay).

## A) Original vs P12 replay vs P12 live

| metric | Original | P12 replay | P12 live |
| --- | --- | --- | --- |
| truthful (final) | 21 | 22 | 24 |
| hallucination-suspect (final) | 1 | 0 | 0 |
| truthful lost | 1 | 0 | 0 |
| hallucination survived | 1 | 0 | 0 |
| UNKNOWN/empty (final) | 48 | 48 | 46 |
| abstain decisions | 32 | 30 | 32 |

NOTE: Original and Replay share identical raw answers (causal policy delta); the Live column has *different* generated answers, so its column is not line-comparable to the other two — compare rates/shape, not per-item.

## B) Live run details

- raw classification baseline: truthful 24, hallucination-suspect 10 of 100
- truthful (final): **24** | hallucination-suspect (final): **0**
- truthful lost: **0** | hallucination survived: **0**
- UNKNOWN/abstain: **32** abstain decisions, **46** empty/UNKNOWN finals
- decision distribution: `{'accept_supported': 18, 'reject_known_false': 14, 'accept_uncertain': 29, 'abstain': 31, 'reject_low_confidence': 5, 'accept_supported_exact': 2, 'abstain_inefficient': 1}`
- P12 epistemic flags fired (live): `{'tie_resolved_exact_correct': 2}`
- answer claims: **100** | atomic claims: **57**
- SPL: admissible **55**, blocked **2** of 57; flags `{'projection_uncertain': 12, 'projection_invalid': 2}`
- extraction JSON status: `{'raw_ok': 100}`
- OpenRouter provider distribution: `{'GMICloud': 20, 'Venice': 2, 'DeepInfra': 2, 'Fireworks': 14, 'SiliconFlow': 19, 'Novita': 14, 'Alibaba': 15, 'Parasail': 4, 'AtlasCloud': 9, 'Together': 1}`
- avg reasoning tokens: **244.6**

## C) Generalization analysis

- **Did the P12 mechanisms fire on new data?** Live epistemic flags: `{'tie_resolved_exact_correct': 2}` — non-zero counts mean the ordering/tie machinery activated on freshly generated answers, not just the recorded ones.
- **Aggregate stability vs original.** Final truthful 21 (orig) vs 24 (live); hallucination survived 1 vs 0; abstain 32 vs 32. Differences here mix the policy change WITH new-generation + provider variance and cannot be attributed to the policy alone (that is what the replay column is for).
- **New error classes?** Inspect the live decision distribution and flags above for decisions/flags that did not appear in the recorded run; any `ambiguous_unresolved` flag would be the first real firing of rule D. (Reported as data, not interpreted beyond what is present.)
- **Replay vs live divergence** is expected: the replay isolates the policy; the live run re-rolls generation and provider routing, so some replay-measured gains can be masked or amplified by that noise.

## D) Honesty / limits

- **New live run** — newly generated answers; NOT the deterministic replay. Provider/generation noise is present again.
- **Not directly causally comparable** to the replay: the live column changes raw answers + providers + policy at once, so per-item or strict causal attribution is not valid (use the replay for that).
- **Heuristic overlap scorer** still defines the labels; approximate.
- **No claim of general truth ability.** This is one limit-100 sample under one scorer; SPL-core unchanged, no new heuristics added.
