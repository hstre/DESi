# Pre-T10 Threshold Calibration — Concept Gate Decision

**Status:** decision artifact for the Pre-T10
Threshold Calibration Patch (v3.120a–v3.120d).
Per the opening directive ("Kein Paper", "Keine
Synthese bis v3.120d") this document records ONLY
the Concept Gate result; no paper change, no new
failure category, no theory.

## Question

> War die Blindness Rule falsch — oder nur um
> 0.011 schlecht kalibriert?

## Concept Gate evaluation

| # | Gate                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | final_far (v3.120d)               | <= 0.10   | **0.111** | ✗ |
| 2 | final_tpr (v3.120d)               | == 1.0    | **1.000** | ✓ |
| 3 | threshold_drift (v3.120b)         | <= 0.05   | **0.230** | ✗ |
| 4 | false_negative_rate (v3.120c)     | == 0      | **0.000** | ✓ |
| 5 | historical_gate_flip_count        | == 0      | **0**     | ✓ |
| 6 | replay_stability (all four)       | == 1.00   | **1.000** | ✓ |

Four of six gates pass; gates 1 and 3 fail.

## Decision

**Pre-T10 bleibt experimentell.** Per the
directive's exact wording — "Wenn eines
scheitert: Pre-T10 bleibt experimentell." — the
failure of gates 1 and 3 keeps the rule out of
"Architekturregel" status. The audit records:

* v3.120a: sweeping the threshold across the
  full ±20% band (0.43..0.65 in 0.01 steps,
  23 cells) finds **zero feasible cells** that
  satisfy both FAR ≤ 0.10 AND TPR == 1.0. At
  TPR = 1.0 the best FAR is 0.111; at FAR = 0
  the best TPR is 0.813. The two false
  positives (text_variance 0.632 / 0.635) sit
  INSIDE the rescuable-pool range
  (0.6..0.639), making the constraints
  mutually unsatisfiable with any single
  text_variance threshold.
* v3.120b: across 50 deterministic bootstrap
  draws the modal threshold (0.542) appears
  56% of the time, but when the sample misses
  the lowest-variance rescuable pool (pid 15)
  the threshold jumps to the next available
  rescuable value, driving max drift to 0.230.
* v3.120c: 10 PYTHONHASHSEED subprocess
  replays show TPR == 1.000 everywhere; zero
  adverse flips; zero false negatives. The
  rule is byte-stable thanks to v3.96c.
* v3.120d: 2 of 6 Concept Gate conditions
  fail; verdict PRE_T10_EXPERIMENTAL.

The 0.011 FAR overshoot is NOT a calibration
error - it is a structural limit of the
single-threshold rule against the current
text_variance feature.

## Findings the documentation must encode

### 1. No single-threshold solution exists (v3.120a)

| Metric                       | Value     | Gate           |
|------------------------------|-----------|----------------|
| sweep_cell_count             | 23        | -              |
| feasible_cell_count          | 0         | -              |
| optimal_threshold            | 0.43      | (best at TPR=1.0)|
| threshold_window             | (-1, -1)  | empty          |
| window_width                 | 0.000     | -              |
| best_far_at_full_tpr         | 0.111     | (= v3.120 baseline) |
| best_tpr_at_zero_far         | 0.813     | (=13/16)       |

Rescuable pool text_variance values include
0.541 (pid 15) and 0.600 (pid 14); unrescuable
false-positive values 0.632 (pid 16) and 0.635
(pid 17) sit BETWEEN the rescuable 0.600 and
0.639 (pid 11). Excluding the false positives
necessarily excludes pids 14 and 15.

### 2. The threshold drifts under bootstrap (v3.120b)

| Metric              | Value     | Gate           |
|---------------------|-----------|----------------|
| bootstrap_seed_count| 50        | -              |
| threshold_mean      | 0.586     | -              |
| threshold_ci        | (0.542, 0.737) | -         |
| threshold_drift     | 0.230     | <= 0.05 ✗      |
| seed_invariance     | 0.560     | -              |

The modal threshold is stable (56% of draws),
but tail draws can shift up to 0.230 - the
audit's lower bound is fragile to
re-sampling.

### 3. Stress replay confirms TPR stability (v3.120c)

| Metric                  | Value     | Gate           |
|-------------------------|-----------|----------------|
| seed_count              | 10        | -              |
| cell_count              | 10        | -              |
| historical_tpr_min      | 1.000     | -              |
| historical_tpr_max      | 1.000     | -              |
| false_negative_rate_max | 0.000     | == 0 ✓         |
| adverse_flip_count      | 0         | == 0 ✓         |

The v3.96c determinism patch keeps every cell
byte-stable; the rule's allowed/blocked
partition is identical across seeds.

### 4. Final verdict (v3.120d)

| Metric                       | Value     | Gate           |
|------------------------------|-----------|----------------|
| final_threshold              | 0.542     | -              |
| final_far                    | 0.111     | <= 0.10 ✗      |
| final_tpr                    | 1.000     | == 1.0 ✓       |
| threshold_drift              | 0.230     | <= 0.05 ✗      |
| adverse_flips                | 0         | -              |
| false_negative_rate          | 0.000     | == 0 ✓         |
| rule_roi                     | 8.26      | -              |
| historical_gate_flip_count   | 0         | == 0 ✓         |
| calibration_window_exists    | False     | -              |
| failing_conditions           | (final_far, threshold_drift) | - |

## Why the "0.011 error" is structural

The single-threshold rule maps the closed
text_variance axis through one cut. The
rescuable and unrescuable populations are NOT
linearly separable along this axis: 2 unrescuable
outliers sit inside the rescuable value range.

A two-feature rule (text_variance combined with
family_count) WOULD separate them - the
unrescuable outliers have family_count = 4 with
text_variance ≈ 0.63, while the comparable
rescuable 4-family pools have text_variance >=
0.77. But the directive constrains the rule to a
single-threshold form, and the bootstrap drift
shows that even at the modal value the rule is
on the edge of its sample stability.

DESi's answer to the directive's closing
question "War die Blindness Rule falsch — oder
nur um 0.011 schlecht kalibriert?":
**Strukturell knapp, nicht knapp kalibriert.** The
single-threshold form has a 0.011 lower bound
on FAR at TPR = 1.0; no calibration can move
that bound. The rule is not "wrong" - it works
operationally (100% recall, ROI 8.26, zero
adverse flips). It is "experimental" because
the strict Concept Gate demands a feasibility
window that does not exist in this data.

## What the documentation must NOT claim

* That T10 has been activated in production.
  T10 remains read-only across v3.120a-d; the
  9-dim StateVector is unchanged.
* That a two-feature rule should be deployed.
  v3.120 / v3.120a-d only audit the existing
  single-threshold rule. Any rule-shape change
  would require its own directive.
* That the v3.120 PROOF that FAR=0.111 is
  reversible. The structural infeasibility
  shown by v3.120a is a property of the
  text_variance distribution, not of the
  threshold choice.
* That bootstrap drift indicates the rule is
  random. The modal threshold appears in 56%
  of draws; the drift only kicks in when the
  bootstrap sample happens to miss pid 15
  (the smallest-variance rescuable pool).
* That a new failure category is introduced.
  The directive explicitly forbids new failure
  categories in this sprint.

## Stop rules and gate signals

* v3.120a `feasible_cell_count` (0) FAIL.
  Documented.
* v3.120b `threshold_drift` (0.230) FAIL.
  Documented.
* v3.120c `historical_tpr_min` (1.000) PASS;
  `adverse_flip_count` (0) PASS. Documented.
* v3.120d `final_far` (0.111) FAIL;
  `final_tpr` (1.000) PASS;
  `historical_gate_flip_count` (0) PASS.
  Documented.
* v3.120a-v3.120d `replay_stability` (1.00)
  PASS.

## Sources

* `artifacts/v3_120a/report.json`                              — threshold sweep
* `artifacts/v3_120a/pre_t10_threshold_sweep.json`             — 23 sweep cells, 0 feasible
* `artifacts/v3_120b/report.json`                              — bootstrap stability
* `artifacts/v3_120b/pre_t10_bootstrap.json`                   — 50 deterministic draws
* `artifacts/v3_120c/report.json`                              — stress replay
* `artifacts/v3_120c/pre_t10_stress_replay.json`               — 10 PYTHONHASHSEED cells
* `artifacts/v3_120d/report.json`                              — final rule decision
* `artifacts/v3_120d/pre_t10_final_rule.json`                  — gate failures: (final_far, threshold_drift)
