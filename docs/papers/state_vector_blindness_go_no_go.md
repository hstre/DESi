# State-Vector Blindness — Concept Gate Decision

**Status:** decision artifact for the State-Vector
Blindness Consolidation sprint (v3.117–v3.120).
Per the opening directive ("Kein Paper", "Keine
Synthese bis v3.120") this document records ONLY
the Concept Gate result; no paper change, no new
failure category, no theory.

## Question

> Wann fehlt DESi wirklich Information — und
> wann schaut es nur nicht genau genug hin?

## Concept Gate evaluation

| # | Gate                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | blindness_pool_count (v3.117)     | > 0       | **52**    | ✓ |
| 2 | semantic_blindness_rate (v3.118)  | > 0       | **0.019** | ✓ |
| 3 | blindness_prediction_auc (v3.119) | >= 0.70   | **0.993** | ✓ |
| 4 | false_activation_rate (v3.120)    | <= 0.10   | **0.111** | ✗ |
| 5 | true_case_recall (v3.120)         | == 1.0    | **1.000** | ✓ |
| 6 | replay_stability (all four)       | == 1.00   | **1.000** | ✓ |

Five of six gates pass; gate 4 fails by 0.011.

## Decision

**Blindness bleibt Sonderfall (strict reading).**
Per the directive's exact wording — "Wenn eines
scheitert: Blindness bleibt Sonderfall." — the
literal failure of gate 4 keeps the proposed
pre-T10 rule out of "architectural rule" status.
The audit records:

* v3.117: 52 cross-family blindness pools in the
  corpus. 393 of 395 trajectories (99.5%) live
  in some pool; the largest pool spans 11
  families and 121 anchors.
* v3.118: most blindness is duplicate-driven
  (65%); 33% structural; 2% (1 pool) is genuine
  semantic blindness like the G/E case.
* v3.119: pool text_variance is a near-perfect
  predictor of T10 rescuability
  (blindness_prediction_auc = 0.993,
  false_negative_rate = 0.000). The
  recoverability threshold sits at 0.542 -
  every rescuable pool has text_variance >= 0.542.
* v3.120: the pinned-threshold pre-T10 rule
  blocks 34 of 52 pools and allows 18; recalls
  100% of genuinely rescuable pools but mistakenly
  allows 2 unrescuable ones (false_activation_rate
  = 0.111).

The strict reading keeps the rule
"overpermissive"; the directional reading notes
that 100% recall with 11% false-activation and
ROI 8.26 still strictly dominates "no rule at
all" (which would activate T10 against every
unrescuable pool).

## Findings the documentation must encode

### 1. Blindness is pervasive (v3.117)

| Metric                   | Value     |
|--------------------------|-----------|
| total_pool_count         | 52        |
| blindness_pool_count     | 52        |
| affected_family_count    | 30        |
| largest_pool_size        | 121       |
| mean_pool_size           | 7.56      |
| total_blind_anchor_count | 393 / 395 |

* The 10-family case from earlier sprints is one
  of 52 cross-family pools; the largest pool
  spans 11 families and 121 anchors; a second
  pool spans 16 families and 78 anchors.
* Only 2 trajectories have a unique state
  signature.

### 2. Most blindness is literal duplication (v3.118)

| Kind                   | Count | Rate    |
|------------------------|-------|---------|
| DUPLICATE_COLLAPSE     | 34    | 0.654   |
| STRUCTURAL_COLLAPSE    | 17    | 0.327   |
| SEMANTIC_COLLAPSE      | 1     | 0.019   |
| ROUTING_COLLAPSE       | 0     | 0.000   |
| UNKNOWN                | 0     | 0.000   |

* 65% of cross-family pools share most of their
  text (literal duplicates across corpus
  versions).
* 33% have partial text overlap (structural
  collisions).
* Only 1 pool is a genuine semantic collapse
  comparable to G/E.

### 3. Pool text variance predicts T10 rescuability (v3.119)

| Metric                       | Value     | Gate           |
|------------------------------|-----------|----------------|
| pool_count                   | 52        | -              |
| rescuable_pool_count         | 16        | -              |
| unrescuable_pool_count       | 36        | -              |
| recoverability_threshold     | 0.542     | -              |
| blindness_prediction_auc     | 0.993     | >= 0.70 ✓      |
| false_positive_rate          | 0.056     | -              |
| false_negative_rate          | 0.000     | -              |

* The text_variance score (1 - mean pairwise
  Jaccard within the pool) ranks every
  rescuable pool above every unrescuable one
  except 2 outliers.
* Setting the threshold at the smallest
  rescuable-pool text_variance yields false-
  negative rate 0 and false-positive rate
  0.056.

### 4. The pre-T10 rule is operational but slightly over-permissive (v3.120)

| Metric                       | Value     | Gate           |
|------------------------------|-----------|----------------|
| blindness_check_threshold    | 0.542     | -              |
| pool_count                   | 52        | -              |
| allowed_pool_count           | 18        | -              |
| blocked_pool_count           | 34        | -              |
| false_activation_rate        | 0.111     | <= 0.10 ✗      |
| true_case_recall             | 1.000     | == 1.0 ✓       |
| historical_gate_flip_count   | 0         | -              |
| rule_roi                     | 8.26      | -              |

* The rule lets through every rescuable pool
  (100% recall) and blocks 34 of 36 unrescuable
  ones (94% specificity).
* The 2 wrongly-allowed pools are unrescuable
  pools that happen to have text_variance
  slightly above the threshold (= just outside
  the duplicate band).
* `historical_gate_flip_count` = 0: the rule
  only blocks NEW T10 activation; it does not
  modify any persisted artifact.

## Why this is "Sonderfall" under the strict gate
## and "operationally valid" under the directional
## reading

The directive's gate 4 (`false_activation_rate
<= 0.10`) is written to keep the rule highly
specific. The measured 0.111 misses it by
0.011 - a single pool out of the 18 allowed
crossings.

A stricter threshold would remove the
false-positives at the cost of also removing
some true positives (since the rescuable and
unrescuable populations overlap on the
text_variance axis). The audit chose the
threshold that preserves 100% recall; any
stricter threshold would push true_case_recall
below 1.0 and fail gate 5 instead.

DESi's answer to the directive's closing
question "Wann fehlt DESi wirklich Information
- und wann schaut es nur nicht genau genug
hin?":
**DESi fehlt wirklich Information, wenn die
Pool-Mitglieder ihre Texte teilen
(DUPLICATE_COLLAPSE, 65% der Faelle) - dann
gibt es nichts zu sehen.** DESi schaut nur nicht
genau genug hin, wenn die Pool-Mitglieder
verschiedene Texte haben (SEMANTIC_COLLAPSE,
2% der Faelle, plus die 33%
STRUCTURAL_COLLAPSE band) - dort koennten neue
Dimensionen die Information herausziehen, bis
zur Grenze des text_variance-Thresholds.

## What the documentation must NOT claim

* That T10 has been activated in production.
  T10 remains read-only across v3.117-v3.120;
  the 9-dim StateVector is unchanged.
* That the rule should be deployed at the
  current threshold. Gate 4 fails by 0.011;
  any deployment requires either a stricter
  threshold (accepting recall loss) or a
  directive that explicitly relaxes the
  0.10 ceiling.
* That semantic blindness is exotic. v3.118
  reports only 1 pool in the SEMANTIC_COLLAPSE
  category, but the STRUCTURAL_COLLAPSE band
  (17 pools, 33%) overlaps with it
  conceptually.
* That state-vector blindness is a bug. The
  representation is a finite-state digest; some
  collapse is inevitable. The audit measures
  the EXTENT of the collapse and the LIMITS of
  T10's recovery.
* That a new failure category is introduced.
  The directive explicitly forbids new failure
  categories in this sprint.

## Stop rules and gate signals

* v3.117 `blindness_pool_count` (52) PASS.
  Documented.
* v3.118 `semantic_blindness_rate` (0.019)
  PASS. Documented.
* v3.119 `blindness_prediction_auc` (0.993)
  PASS. Documented.
* v3.120 `false_activation_rate` (0.111)
  FAIL; `true_case_recall` (1.000) PASS.
  Documented.
* v3.117-v3.120 `replay_stability` (1.00)
  PASS.

## Sources

* `artifacts/v3_117/report.json`                              — blindness census
* `artifacts/v3_117/state_blindness_census.json`              — 52 pools, 393 anchors
* `artifacts/v3_118/report.json`                              — blindness taxonomy
* `artifacts/v3_118/state_blindness_taxonomy.json`            — 52 pools classified
* `artifacts/v3_119/report.json`                              — T10 scope boundary
* `artifacts/v3_119/t10_scope_boundary.json`                  — recoverability_threshold 0.542
* `artifacts/v3_120/report.json`                              — pre-T10 rule
* `artifacts/v3_120/pre_t10_rule.json`                        — rule_roi 8.26
