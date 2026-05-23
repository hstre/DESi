# Paper 11 — Complementarity Go / No-Go Decision

**Status:** decision artifact for the Epistemic
Complementarity Audit Sprint (v3.61–v3.64). The
directive's opening "Paper 11 bleibt pausiert" is
respected: this document records that the Concept Gate
for the complementarity hypothesis is MET, but Paper
11 still awaits explicit user authorisation to be
written.

## Concept Gate evaluation (directive § "Paper-11 Gate v3")

| # | Gate                                                | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | replay_stability (all sprints)                      | == 1.00   | **1.00**  | ✓ |
| 2 | distance_only_activation < combined_activation (v3.61) | <         | **0.423 < 0.633** | ✓ |
| 3 | coverage_gain (v3.62)                               | > 0       | **6.55**  | ✓ |
| 4 | diversity_activation_correlation (v3.63)            | > 0       | **0.027** | ✓ |
| 5 | at least one necessary_factor identified (v3.64)    | exists    | **A_distance + D_coverage_gain** | ✓ |

**All five Concept Gates pass.**

## Decision

**Concept Gate: PASS.** The four field-amplification
factors examined here — distance, corpus
heterogeneity, failure diversity, and coverage gain —
together explain the v3.50 resonance phenomenon, with
two factors (distance and coverage gain) identified
as causally necessary by the v3.64 ablation harness.
The complementarity hypothesis is empirically grounded:

> Field amplification is driven by epistemic
> complementarity, not semantic resonance.

The phenomenon previously called "pair resonance" in
v3.50 is more accurately:

> **Coverage-gain-driven activation, enabled by
> geometric distance between anchors, modulated by
> corpus heterogeneity, weakly tracked by failure
> diversity.**

Paper 11 may be written when the user requests it;
this document is the Concept Gate decision, not the
paper.

## Sources

* `artifacts/v3_61/report.json`                           — distance vs complementarity
* `artifacts/v3_61/complementarity_vs_distance.json`      — 4-cell distance × family grid
* `artifacts/v3_62/report.json`                           — blind-spot mapping
* `artifacts/v3_62/blindspot_mapping.json`                — 190 per-pair coverage records
* `artifacts/v3_63/report.json`                           — failure diversity
* `artifacts/v3_63/failure_diversity.json`                — 20 profiles + 190 pair_records
* `artifacts/v3_64/report.json`                           — causal complementarity
* `artifacts/v3_64/causal_complementarity.json`           — 4-factor ablation results

## Findings the paper must encode

### 1. Distance is necessary but not sufficient (v3.61)

| Distance | Family   | Pairs | Resonant | Rate  |
|----------|----------|-------|----------|-------|
| high_d   | same_fam | 28    | 14       | 0.500 |
| low_d    | same_fam | 26    | 2        | 0.077 |
| high_d   | diff_fam | 60    | 38       | 0.633 |
| low_d    | diff_fam | 76    | 10       | 0.132 |

* `distance_only_activation` = 0.423
* `heterogeneity_only_activation` = 0.055
* `combined_activation` = 0.633
* `baseline_activation` = 0.077
* `best_explanation_model` = COMBINED

Distance is the dominant single factor (0.42 effect)
but combined activation (0.63) strictly exceeds
distance alone, so heterogeneity adds a real
interaction effect. The directive's killer
question — "Ist Complementarity nur Distanz?" — is
answered NO.

### 2. Heterogeneous anchor pairs cover new claim regions (v3.62)

| Cohort         | active | mean_gain | mean_red | new_frac |
|----------------|--------|-----------|----------|----------|
| heterogeneous  | 88     | 6.55      | 0.455    | 0.545    |
| homogeneous    | 32     | 6.00      | 0.500    | 0.500    |

* `coverage_gain` = 6.55 (heterogeneous cohort)
* `redundancy_score` = 0.455 (vs 0.500 for
  homogeneous)
* `new_region_fraction` = 0.545 (vs 0.500 for
  homogeneous)
* `uncovered_before` = 145
* `uncovered_after` = 12 (hard blind spots even with
  the full 20-anchor manifold)

Heterogeneous pairs are empirically less redundant
and add more new claim regions, though by modest
margins (~5% redundancy reduction). The directive's
"Erweitern heterogene Paare wirklich den Loesungs-
raum?" is answered YES.

### 3. Failure diversity weakly predicts activation (v3.63)

* `failure_diversity_score` = 0.442 (global average
  across all 190 pairs, normalised by max 5 axes)
* `redundancy_score` = 0.558
* `diversity_activation_correlation` = 0.027
* `mean_diversity_resonant` = 2.25
* `mean_diversity_non_resonant` = 2.19

The correlation is positive (Paper-11 v3 gate #4
PASS by direction) but small. Diversity is a
contributing but minor factor — distance and
coverage gain dominate the variance.

### 4. Causal ablation identifies necessary factors (v3.64)

Ordered by causal_importance:

| Factor             | Subset | Resonant After | Rate After | Importance | Low Power |
|--------------------|--------|----------------|------------|------------|-----------|
| D_coverage_gain    | 126    | 0              | 0.000      | 1.000      | No        |
| C_diversity        | 6      | 0              | 0.000      | 1.000      | YES       |
| A_distance         | 102    | 12             | 0.118      | 0.651      | No        |
| B_heterogeneity    | 54     | 16             | 0.296      | 0.120      | No        |

* `necessary_factors` = (A_distance, D_coverage_gain)
* `sufficient_factors` = () — no single factor's
  presence alone produces resonance with all others
  ablated; the relevant subsets are empty given the
  entanglement
* `causal_importance` = {D: 1.00, C: 1.00 [LP],
  A: 0.65, B: 0.12}
* `activation_after_ablation` = {D: 0, C: 0, A: 12,
  B: 16}

D_coverage_gain is necessary by construction
(resonance requires non-empty symmetric difference,
which IS coverage_gain > 0). A_distance is necessary
empirically (ablation drops rate by 65%).
B_heterogeneity is a modest contributor (12%
importance). C_diversity flags 100% importance but
has a tiny 6-pair subset (LOW_POWER).

## Why this is GO (Concept Gate) but not yet Paper

All five Concept Gates pass empirically. The
directive's "Paper 11 bleibt pausiert" remains in
force as a user-level pause, not a gate-level halt.
The decision artifact records:

* the complementarity hypothesis is empirically
  supported on this corpus
* the v3.50 resonance phenomenon has a structural
  explanation (coverage-gain enabled by distance,
  modulated by heterogeneity)
* DESi's answer to "Warum verstaerken nur
  epistemisch unterschiedliche Anker das Feld?":
  because complementary anchors cover non-redundant
  claim regions; the activation requires both
  geometric distance and non-empty coverage gain.

When the user authorises Paper 11, the paper must
include:

* The v3.50 "semantic resonance" finding (96 method-
  only resonant pairs)
* The v3.54 falsification (per-corpus resonance = 0)
* The v3.57 entanglement (content/method overlap
  0.994)
* The v3.60 killer-cell finding (all resonance in
  diff_c/diff_m)
* The v3.61-v3.64 reframing: complementarity, not
  resonance
* The causal ablation table from v3.64 as the
  structural explanation

## What the paper must NOT claim

* That "semantic coupling" is the right name for
  the phenomenon. v3.50–v3.60 falsified that
  framing. The phenomenon is coverage-gain-driven
  activation.
* That distance is the only factor. v3.61 shows
  heterogeneity adds 0.13 absolute activation above
  distance alone.
* That diversity is causally important. v3.63 shows
  only weak correlation (0.027); v3.64 cannot
  cleanly assess C_diversity because the
  zero-diversity subset has only 6 pairs (low
  power).
* That the necessary factors generalise to other
  corpora. v3.54 already showed pair structure is
  corpus-local; the same caveat applies to the
  complementarity findings reported here.
* That coverage_gain being necessary is a deep
  finding. It is necessary by construction:
  resonance is DEFINED as
  proper-set-independence which REQUIRES non-empty
  symmetric difference, which IS coverage_gain > 0.
  The non-trivial finding is A_distance's 0.65
  importance and B_heterogeneity's 0.12 modulation.

## Stop rules not triggered

* v3.61 `replay_stability` (1.00) PASS.
* v3.61 distance_only (0.423) ≠ combined (0.633)
  → COMPLEMENTARITY_BEYOND_DISTANCE.
* v3.62 `replay_stability` (1.00) PASS.
* v3.62 `coverage_gain` (6.55) > 0.
* v3.63 `replay_stability` (1.00) PASS.
* v3.63 `diversity_activation_correlation` (0.027)
  > 0.
* v3.64 `replay_stability` (1.00) PASS.
* v3.64 `necessary_factors` non-empty (A_distance,
  D_coverage_gain).
