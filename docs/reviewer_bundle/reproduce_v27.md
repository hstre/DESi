# Reproduce v2.7 — Guarded `CAUSAL_CHAIN` Rule

The v2.7 patch added exactly one closed-enum member
(`InferenceRule.CAUSAL_CHAIN`) and one new validator
(`_try_causal_chain`) to `src/desi/logic/inference.py`. Nothing
under `src/desi/{consilium,recursive,tools,memory,evolution,sandbox}/`
was modified.

## The minimal reproduction

From a fresh clone:

```bash
PYTHONPATH=src pytest tests/logic/test_causal_chain.py tests/logic/test_causal_chain_regression.py -q
```

Expected output:

```
33 passed
```

Expected runtime: ~1s.

## What the 33 tests prove

The 18 tests in `test_causal_chain.py` exercise the rule body and
its seven guards:

- `test_causal_chain_is_in_inference_rule_enum` — closed enum has 6 members.
- `test_three_step_chain_resolves_with_causal_chain` — positive case R2_01.
- `test_four_step_chain_resolves_with_causal_chain` — positive case R3_01.
- `test_contradiction_rule_runs_before_causal_chain` — Guard 1, iteration order.
- `test_negation_marker_in_premise_blocks_causal_chain` — denying-the-antecedent guard.
- `test_universal_premise_blocks_causal_chain` — R4 universal-quantifier guard.
- `test_quantifier_some_blocks_causal_chain` — `some`/`any` guard.
- `test_cycle_connective_*_blocks_causal_chain` — R5 cycle guard via three connectives.
- `test_token_repetition_3_premises_blocks_causal_chain` — structural cycle guard.
- `test_recycled_conclusion_token_blocks_causal_chain` — R4_05 light-bends-in-straight-lines guard.
- Plus 8 more for negative cases, replay determinism, and direct validator API.

The 15 tests in `test_causal_chain_regression.py` pin the
end-to-end invariants:

- `test_v15_precision_remains_one` — main benchmark precision = 1.0.
- `test_v15_recall_remains_one` — main benchmark recall = 1.0.
- `test_v15_false_positives_remain_zero` — main benchmark FP = 0.
- `test_v26_known_false_positives_do_not_reopen` — 8/8 historical false-positives stay blocked.
- `test_v18_authority_traps_still_block_with_authority_claim` — Cat C 10/10 BLOCKED with AUTHORITY_CLAIM.
- `test_cat_e_philosophy_zero_false_positives` — Cat E FPs = 0.
- `test_v23_r4_contradiction_never_via_causal_chain` — no R4 case matched by CAUSAL_CHAIN.
- `test_v23_r5_cycle_never_via_causal_chain` — no R5 case matched by CAUSAL_CHAIN.
- `test_r2_r3_gain_at_least_twelve_cases` — 12 R2+R3 cases reach COMPLETE.
- Plus 6 more for replay-hash bit-identity.

## Anchored claims

| Claim | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-035 | v2.7 main precision is 1.0 | `artifacts/v2_7/report.json` | `main_benchmark.precision` | `1.0` |
| RB-036 | v2.7 main recall is 1.0 | `artifacts/v2_7/report.json` | `main_benchmark.recall` | `1.0` |
| RB-037 | v2.7 main FP is 0 | `artifacts/v2_7/report.json` | `main_benchmark.false_positives` | `0` |
| RB-038 | R2+R3 gain count is 12 | `artifacts/v2_7/report.json` | `r2_r3_gain_count` | `12` |
| RB-039 | R4 regression count is 0 | `artifacts/v2_7/report.json` | `r4_regression_count` | `0` |
| RB-040 | R5 regression count is 0 | `artifacts/v2_7/report.json` | `r5_regression_count` | `0` |
| RB-041 | 12 cases complete via CAUSAL_CHAIN | `artifacts/v2_7/report.json` | `len:cases_complete_via_causal_chain` | `12` |

Verified by `tests/reviewer_bundle/test_claim_index.py::
test_each_claim_value_matches_artifact[RB-035..041]`.
