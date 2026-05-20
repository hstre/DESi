# DESi v3.124 — Full Regression + Gate Deployment Validation

**Killerfrage:** Ist Pre-T10 v2 jetzt wirklich architekturreif — oder nur lokal perfekt?

**Verdict:** `DEPLOYED_ARCHITECTURE_RULE`

## Full regression result

```
5024 passed in 3592.47s (0:59:52)
```

The full suite (`pytest tests/`) completed cleanly with 5024 passing tests, 0 failures, 0 errors, in 59:52. This includes every T10, blindness, degeneracy, proxy-audit, and historical-replay sprint in the repository, run with the multi-signal pre-T10 rule active.

A single brittle test surfaced on the first run — `tests/runtime_audit/test_v3_121.py::test_artifact_report_matches_live_build` — because it pinned per-host hardware fingerprints (`cpu_model` "@ 2.80GHz") against a live probe on a different VM ("@ 2.10GHz"). It was relaxed in commit `03e96b3` to compare only the derived classification fields (`runner_type`, `ci_env`, `halt`, `machine`, `recommendation`, `replay_stability`) — the same pattern v3.122 uses for commit-count drift. The substantive regression was clean before and after.

## Pflichtmetriken

| Metric | Value | Gate |
|---|---|:---:|
| `full_regression_passed` | `true` | ✓ |
| `historical_tpr` | 1.000000 | ✓ |
| `historical_far` | 0.000000 | ✓ |
| `adverse_flip_count` | 0 | ✓ |
| `hash_stability` | 1.000000 | ✓ |
| `rule_roi` | 100.0 | ✓ |

All 6 gates green. `failing_conditions = []`.

## Pflichtfragen

1. **Bleibt TPR = 1.0?** JA — `historical_tpr = 1.0` against the v3.119 ground truth (16 of 16 rescuable cross-family pools allowed through).
2. **Bleibt FAR = 0?** JA — `historical_far = 0.0`. Zero unrescuable pools leaked through the rule.
3. **Entstehen adverse flips?** NEIN — `adverse_flip_count = 0`. No rescuable case is silently dropped by the new rule.
4. **Bleiben Replay-Hashes stabil?** JA — the two pinned v2.8 determinism invariants both hold: `v2_8_reconstruction = 1f4d9dfe44cb16e1`, `v2_8_failcase = d83d81ab8417c022`. `hash_stability = 1.0` over 2 pinned checks.
5. **Gibt es neue Blindness-Leaks?** NEIN — the rule's allowed set (16 pools) is a strict subset of the v3.120 single-threshold allowed set (18 pools); the 2 removed pools are exactly the 2 false positives that v3.120 leaked. No new pool slips through.
6. **Bleibt ROI positiv?** JA — `rule_roi = 100.0` (`true_case_recall / (false_activation_rate + 0.01)`).

## Pre-existing drift (info-only, not a gate)

The v4.x replay matrix entries (`v4_0` through `v4_8`) report `hash_equal = false`. This is documented `HISTORICAL_RUNTIME_DRIFT` under v4.11 and predates the multi-signal rule by many sprints. The v3.124 validation surfaces it as `matrix_drift_count = 9` for the audit trail but does NOT include it in `hash_stability`, because doing so would falsely attribute pre-existing drift to the new rule.

## Replayed sprints

Every sprint with persisted tests in the repo replayed with the multi-signal rule active. Highlights:

* **T10 sprints**: `t10`, `t10_adaptive`, `t10_boundary`, `t10_compat`, `t10_deep`, `t10_directional`, `t10_gate`, `t10_generalization`, `t10_inject`, `t10_proxy`, `t10_redecision`, `t10_redeployment`, `t10_rename`, `t10_roi`, `t10_semantic`, `t10_single_structural`, `t10_stress`, `t10_structural_vocab`, `t10_transfer`, `t10_verdict`, `t10_vocabulary` — all green.
* **Blindness sprints**: `state_blindness`, `state_blindness_taxonomy`, `blind_spot_mapping`, `missing_blind` — all green.
* **Degeneracy sprints**: `predictive_degeneracy`, `taxonomy_generalization`, `taxonomy_stability` — all green.
* **Proxy audits**: `t10_proxy`, `causal_probe`, `causal_naturalness`, `causal_redteam`, `causal_complementarity`, `causal_link_typing`, `external_audit_probe`, `external_probe`, `repro_audit` — all green.
* **Historical replay chains**: `self_audit`, `gate_order`, `frame_invariance`, `frames`, `frame_disambiguator_probe`, `frame_inference`, `frame_tension`, `determinism_replay`, `determinism_patch`, `content_inversion_patch`, `bidirectional_cycle_patch` — all green, with the pinned v2.8 hashes intact.
* **Pre-T10 stack**: `pre_t10_rule`, `pre_t10_calibration`, `pre_t10_bootstrap`, `pre_t10_stress`, `pre_t10_final`, `pre_t10_v2`, `pre_t10_v2_deploy`, `pre_t10_v2_validation` — all green.

## Deployment

All six gates pass. Per the directive's deployment rule, the multi-signal pre-T10 rule is now:

> **Pre-T10 v2 = deployed architecture rule**

The rule:
```
allow_t10(pool)  ⇔  text_variance(pool) ≥ 0.541667
                    AND members_per_family(pool) ≥ 1.5
```

Replay-stable, deterministic, two interpretable thresholds, zero false activations and full recall on the v3.119 ground truth, no adverse flips on the full historical replay, pinned hashes intact, ROI = 100. The rule moves from EXPERIMENTAL to DEPLOYED.
