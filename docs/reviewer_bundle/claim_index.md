# Reviewer-Bundle Claim Index (60 claims)

Every claim below is machine-checked by
`tests/reviewer_bundle/test_claim_index.py`. The canonical source
is `claim_index.json`; this document is a human-readable rendering.

Schema: each row has a deterministic ``claim_id``, a plain
statement, and three resolution fields (`artifact_path`,
`field_path`, `expected_value`). When the supporting artefact
carries its own `replay_hash`, that is also listed.

---

## v2.0 — Evolution Sandbox

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-001 | v2.0 sandbox accepted all 30 mutation steps. | `artifacts/v2_0/report.json` | `accepted_steps` | `30` |
| RB-002 | v2.0 sandbox killed zero steps. | `artifacts/v2_0/report.json` | `killed_steps` | `0` |
| RB-003 | v2.0 sandbox left stable v1.9 source fingerprint unchanged. | `artifacts/v2_0/report.json` | `stable_hash_before==stable_hash_after` | `true` |
| RB-004 | v2.0 sandbox drift not detected. | `artifacts/v2_0/report.json` | `drift_detected` | `false` |
| RB-005 | v2.0 sandbox best parameter value. | `artifacts/v2_0/report.json` | `best_parameter_value` | `0.47` |

## v2.1 — Self-Diagnostic

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-006 | v2.1 diagnostic reports 2 actionable deficits. | `artifacts/v2_1/report.json` | `actionable_deficits` | `2` |
| RB-007 | v2.1 diagnostic highest severity is 1.0. | `artifacts/v2_1/report.json` | `highest_severity` | `1.0` |
| RB-008 | v2.1 diagnostic highest confidence is 1.0. | `artifacts/v2_1/report.json` | `highest_confidence` | `1.0` |

## v2.2 — Depth Sandbox

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-009 | v2.2 depth-sandbox best_depth equals 1 (Occam). | `artifacts/v2_2/report.json` | `best_depth` | `1` |
| RB-010 | v2.2 depth-sandbox best_fitness is 5.0 across all depths. | `artifacts/v2_2/report.json` | `best_fitness` | `5.0` |
| RB-011 | v2.2 depth-sandbox oscillation detected. | `artifacts/v2_2/report.json` | `oscillation_detected` | `true` |
| RB-012 | v2.2 depth-sandbox accepted all 30 steps. | `artifacts/v2_2/report.json` | `accepted_steps` | `30` |

## v2.3 — Multi-Step Benchmark

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-013 | v2.3 multistep recursion usage rate. | `artifacts/v2_3/report.json` | `metrics.recursion_usage_rate` | `0.033333` |
| RB-014 | v2.3 multistep false_depth_zero_rate. | `artifacts/v2_3/report.json` | `metrics.false_depth_zero_rate` | `1.0` |
| RB-015 | v2.3 multistep cycle_detection_rate. | `artifacts/v2_3/report.json` | `metrics.cycle_detection_rate` | `0.0` |
| RB-016 | v2.3 multistep total cases. | `artifacts/v2_3/report.json` | `metrics.total` | `30` |

## v2.4 — Bridge-Entry Audit

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-017 | v2.4 dominant loss stage. | `artifacts/v2_4/report.json` | `dominant_loss_stage` | `parser_loss` |
| RB-018 | v2.4 recursion_reach_rate. | `artifacts/v2_4/report.json` | `recursion_reach_rate` | `0.033333` |
| RB-019 | v2.4 bridge_creation_rate. | `artifacts/v2_4/report.json` | `bridge_creation_rate` | `0.166667` |
| RB-020 | v2.4 consilium_call_rate. | `artifacts/v2_4/report.json` | `consilium_call_rate` | `0.2` |
| RB-021 | v2.4 resolver_entry_rate. | `artifacts/v2_4/report.json` | `resolver_entry_rate` | `0.2` |
| RB-022 | v2.4 total cases scanned. | `artifacts/v2_4/report.json` | `total_cases` | `30` |

## v2.5 — Inference Rule Coverage

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-023 | v2.5 dominant missing rule class. | `artifacts/v2_5/report.json` | `dominant_missing_rule_class` | `causal_chain` |
| RB-024 | v2.5 rule_hit_rate. | `artifacts/v2_5/report.json` | `rule_hit_rate` | `0.0` |
| RB-025 | v2.5 no_rule_match_rate. | `artifacts/v2_5/report.json` | `no_rule_match_rate` | `1.0` |
| RB-026 | v2.5 parser_vs_rule_misclassification_rate. | `artifacts/v2_5/report.json` | `parser_vs_rule_misclassification_rate` | `0.766667` |
| RB-027 | v2.5 total cases. | `artifacts/v2_5/report.json` | `total_cases` | `30` |

## v2.6 — Causal-Chain Probe

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-028 | v2.6 safe_to_implement. | `artifacts/v2_6/report.json` | `safe_to_implement` | `true` |
| RB-029 | v2.6 known_false_positive_reopen_rate. | `artifacts/v2_6/report.json` | `metrics.known_false_positive_reopen_rate` | `0.0` |
| RB-030 | v2.6 authority_touch_rate. | `artifacts/v2_6/report.json` | `metrics.authority_touch_rate` | `0.0` |
| RB-031 | v2.6 philosophy_touch_rate. | `artifacts/v2_6/report.json` | `metrics.philosophy_touch_rate` | `0.0` |
| RB-032 | v2.6 metaphor_touch_rate. | `artifacts/v2_6/report.json` | `metrics.metaphor_touch_rate` | `0.0` |
| RB-033 | v2.6 multistep_trigger_rate. | `artifacts/v2_6/report.json` | `metrics.multistep_trigger_rate` | `0.733333` |
| RB-034 | v2.6 total cases probed (50 main + 30 multistep). | `artifacts/v2_6/report.json` | `total_cases` | `80` |

## v2.7 — Guarded `CAUSAL_CHAIN`

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-035 | v2.7 main_benchmark precision. | `artifacts/v2_7/report.json` | `main_benchmark.precision` | `1.0` |
| RB-036 | v2.7 main_benchmark recall. | `artifacts/v2_7/report.json` | `main_benchmark.recall` | `1.0` |
| RB-037 | v2.7 main_benchmark false_positives. | `artifacts/v2_7/report.json` | `main_benchmark.false_positives` | `0` |
| RB-038 | v2.7 R2+R3 gain count. | `artifacts/v2_7/report.json` | `r2_r3_gain_count` | `12` |
| RB-039 | v2.7 R4 regression count. | `artifacts/v2_7/report.json` | `r4_regression_count` | `0` |
| RB-040 | v2.7 R5 regression count. | `artifacts/v2_7/report.json` | `r5_regression_count` | `0` |
| RB-041 | v2.7 cases complete via CAUSAL_CHAIN. | `artifacts/v2_7/report.json` | `len:cases_complete_via_causal_chain` | `12` |

## v2.8 — Rule-Patch Protocol

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-042 | v2.8 reconstruction phase. | `artifacts/v2_8/reconstruction.json` | `phase` | `complete` |
| RB-043 | v2.8 reconstruction passed flag. | `artifacts/v2_8/reconstruction.json` | `passed` | `true` |
| RB-044 | v2.8 reconstruction guards declared. | `artifacts/v2_8/reconstruction.json` | `len:created_guards` | `7` |
| RB-045 | v2.8 reconstruction touched files. | `artifacts/v2_8/reconstruction.json` | `len:touched_files` | `8` |
| RB-046 | v2.8 benchmark hashes before==after. | `artifacts/v2_8/reconstruction.json` | `benchmark_hash_before==benchmark_hash_after` | `true` |
| RB-047 | v2.8 reconstruction fail_reason empty. | `artifacts/v2_8/reconstruction.json` | `fail_reason` | `""` |
| RB-048 | v2.8 fake-case phase. | `artifacts/v2_8/fail_case.json` | `phase` | `guard_synthesis` |
| RB-049 | v2.8 fake-case passed flag. | `artifacts/v2_8/fail_case.json` | `passed` | `false` |
| RB-050 | v2.8 fake-case fail_reason. | `artifacts/v2_8/fail_case.json` | `startswith:fail_reason` | `missing_guards` |
| RB-051 | v2.8 fake-case guards. | `artifacts/v2_8/fail_case.json` | `len:created_guards` | `0` |

## v3.0 — Self Paper Audit

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-052 | v3.0 audit total documents. | `artifacts/v3_0/report.json` | `total_documents` | `35` |
| RB-053 | v3.0 audit drift findings count. | `artifacts/v3_0/report.json` | `drift_findings_count` | `0` |
| RB-054 | v3.0 audit hash mismatch claims count. | `artifacts/v3_0/report.json` | `hash_mismatch_claims` | `0` |

## v3.1 — Claim-Anchor Discipline

| ID | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-055 | v3.1 audit drift findings count. | `artifacts/v3_1/audit.json` | `drift_findings_count` | `0` |
| RB-056 | v3.1 audit hash mismatch claims count. | `artifacts/v3_1/audit.json` | `hash_mismatch_claims` | `0` |
| RB-057 | v3.1 anchor total. | `artifacts/v3_1/anchors.json` | `total_anchors` | `36` |
| RB-058 | v3.1 anchor verified. | `artifacts/v3_1/anchors.json` | `verified_anchors` | `36` |
| RB-059 | v3.1 anchor invalid. | `artifacts/v3_1/anchors.json` | `invalid_anchors` | `0` |
| RB-060 | v3.1 legacy exemptions. | `artifacts/v3_1/anchors.json` | `legacy_exemptions` | `19` |

---

**60 claims total.** Verified by
`tests/reviewer_bundle/test_claim_index.py`.
