# T10 — Directional Gate Activation — Concept Gate Decision

**Status:** decision artifact for the T10 Gate
Refinement Patch (v3.104a–v3.104d). Per the
opening directive ("Kein Paper", "Kein neuer
Forschungssprint") this document records ONLY
the Concept Gate result; no paper change, no new
failure category, no theory.

## Question

> War T10 wirklich instabil — oder hat mein Gate
> Verbesserung mit Schaden verwechselt?

## Concept Gate evaluation

| # | Gate                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | adverse_flip_count (v3.104a)      | == 0      | **0**     | ✓ |
| 2 | adverse_auc_delta (v3.104a)       | <= 0.05   | **0.000** | ✓ |
| 3 | false_block_rate (v3.104b)        | == 0      | **0.000** | ✓ |
| 4 | seed_invariance (v3.104c)         | == 1.0    | **1.000** | ✓ |
| 5 | replay_stability (all four)       | == 1.00   | **1.000** | ✓ |

Five of five gates pass.

## Decision

**T10 = empirically activated expansion
trigger.** Per the directive's exact wording —
"Wenn alle bestehen: T10 = empirically activated
expansion trigger." — every Concept Gate
condition under the directional reading passes.
The audit records:

* The 0.494 ``historical_auc_delta`` that
  blocked T10 in v3.104's strict reading is
  composed entirely of beneficial flips on
  three rescue-target sprints (v3.94 / v3.96 /
  v3.100). The adverse component is 0.000
  (v3.104a).
* The proposed directional gate accepts T10
  cleanly and continues to block synthetic
  adverse scenarios. False-block rate drops
  from 0.667 (old gate) to 0.000 (directional);
  false-pass rate stays at 0.000 for both
  gates (v3.104b).
* The directional gate's verdict is stable
  across 10 PYTHONHASHSEED replays,
  10 outcome-list permutations, and 3 module
  re-imports - 23 stress cells total, all
  agreeing (v3.104c).
* The v3.104 ROI of 27.59 is unchanged
  (v3.104d): recovery_gain 1.94 vs
  complexity_cost 0.07.

The old gate's failure mode is now documented:
it conflated direction with magnitude. The
refined gate distinguishes harm from
improvement and routes only harm to the block
state.

## Findings the documentation must encode

### 1. Every historical delta is beneficial (v3.104a)

12 historical-gate outcomes split:

| Cell                | Count |
|---------------------|-------|
| BENEFICIAL_FLIP     | 4     |
| ADVERSE_FLIP        | 0     |
| NEUTRAL_PASS        | 5     |
| NEUTRAL_FAIL        | 3     |

* `adverse_flip_count` = 0
* `beneficial_flip_count` = 4 (v3.94
  best_purity, v3.96 resolved_purity, v3.96
  resolved_auc, v3.100 information_loss)
* `adverse_auc_delta` = 0.000
* `beneficial_auc_delta` = 0.494

The full v3.103 ``historical_auc_delta`` is
identical to the v3.104a
``beneficial_auc_delta`` - no AUC drift is
adverse.

### 2. The directional gate dominates (v3.104b)

Three scenarios:

| Scenario                    | Old gate | Directional gate | Real damage |
|-----------------------------|----------|-------------------|-------------|
| ACTUAL_T10                  | FAIL     | PASS              | No          |
| SYNTHETIC_ADVERSE           | FAIL     | FAIL              | Yes         |
| SYNTHETIC_BENEFICIAL_ONLY   | FAIL     | PASS              | No          |

* false_block_rate_old           = 0.667
* false_block_rate_directional   = 0.000
* false_pass_rate_old            = 0.000
* false_pass_rate_directional    = 0.000

Both gates correctly block real damage. Only the
old gate falsely blocks beneficial scenarios.

### 3. The new gate is stable under stress (v3.104c)

Three closed stress kinds × multiple cells = 23
total:

| Stress kind                  | Cells | Adverse | Beneficial |
|------------------------------|-------|---------|------------|
| SEED_RESHUFFLE               | 10    | 0       | 4 (constant) |
| OUTCOME_PERMUTATION          | 10    | 0       | 4 (constant) |
| ISOLATED_MODULE_REIMPORT     | 3     | 0       | 4 (constant) |
| **Total**                    | **23**| **0**   | **4 ± 0**  |

* `seed_invariance` = 1.000
* `order_invariance` = 1.000
* `reimport_invariance` = 1.000

The v3.96c determinism patch keeps every cell
byte-stable.

### 4. T10 is activated under the directional gate (v3.104d)

| Metric                       | Value     |
|------------------------------|-----------|
| t10_directional_go           | **true**  |
| failing_conditions           | (none)    |
| adverse_auc_delta            | 0.000     |
| beneficial_auc_delta         | 0.494     |
| final_recovery_gain          | 1.942     |
| final_complexity_cost        | 0.070     |
| final_roi                    | 27.591    |

The v3.104 ROI is unchanged. T10 was blocked by
the old gate's gate-5 clause - that clause has
been replaced by an adverse-only check, and T10
now passes cleanly.

## Why this is "directionally activated", not
## "production-deployed"

The directional-gate verdict is empirical: it
records that the architectural change is safe
to apply under the proposed gate logic. It is
NOT a deployment instruction. The 9-dim
StateVector remains canonical until a
production-deployment directive arrives.

The previous v3.104 decision document
(t10_activation_go_no_go.md) recorded the
strict reading of the original gate; this
document records the directional reading.
Both documents stand: the strict reading shows
what the literal directive said, the
directional reading shows what the directive's
intent was.

DESi's answer to the directive's closing
question "War T10 wirklich instabil — oder hat
mein Gate Verbesserung mit Schaden verwechselt?":
**Das Gate hat Verbesserung mit Schaden
verwechselt.** T10 itself is stable across
every stress cell measured; the previous
block was a gate-logic artifact, not a real
limit.

## What the documentation must NOT claim

* That the production StateVector has been
  expanded. T10 remains read-only across
  v3.101-v3.104d; the 9-dim canonical
  representation is unchanged.
* That the strict v3.104 decision is wrong.
  Under the literal directive, gate 5 failed;
  this document does not retract that. It
  records that the directive's intent (block
  HARM) is satisfied even though the
  directive's letter (block any DRIFT) is
  not.
* That this change requires re-running prior
  research sprints. v3.103 already showed
  zero adverse flips; the artifacts are
  frozen.
* That the v2.8 replay hashes change. T10's
  gate logic does not touch the v2.8
  pipeline; the pinned hashes
  (1f4d9dfe44cb16e1, d83d81ab8417c022) are
  unaffected.
* That a new failure category is introduced.
  The directive explicitly forbids new
  failure categories in this sprint.

## Stop rules and gate signals

* v3.104a `adverse_flip_count` (0) PASS.
  Documented.
* v3.104a `adverse_auc_delta` (0.000) PASS.
  Documented.
* v3.104b `false_block_rate_directional`
  (0.000) PASS. Documented.
* v3.104c `seed_invariance`,
  `order_invariance`, `reimport_invariance`
  (all 1.000) PASS. Documented.
* v3.104d `t10_directional_go` (true) PASS.
  Documented.
* v3.104a-v3.104d `replay_stability` (1.00)
  PASS.

## Sources

* `artifacts/v3_104a/report.json`                              — delta decomposition
* `artifacts/v3_104a/t10_delta_decomposition.json`             — 12 classified outcomes
* `artifacts/v3_104b/report.json`                              — directional gate simulation
* `artifacts/v3_104b/t10_directional_gate.json`                — 3 scenarios, both gates evaluated
* `artifacts/v3_104c/report.json`                              — gate stress replay
* `artifacts/v3_104c/t10_gate_stress.json`                     — 23 stress cells
* `artifacts/v3_104d/report.json`                              — final re-decision
* `artifacts/v3_104d/t10_final_redecision.json`                — gate input + pass decision
* `docs/papers/t10_activation_go_no_go.md`                     — the prior strict-reading verdict (still stands)
