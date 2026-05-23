# Redundancy Masking Probe — Concept Gate Decision

**Status:** decision artifact for the Redundancy
Masking Probe Sprint (v3.78–v3.80). Per the
directive's opening "Kein Paper", this document
records ONLY the concept-gate result. No paper
change.

## Concept Gate evaluation (directive § "Concept Gate")

| # | Gate                                            | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | single_removal_perturbation (v3.78)             | == 0      | **0**     | ✓ |
| 2 | double_removal_perturbation (v3.78)             | > 0       | **121**   | ✓ |
| 3 | redundancy_unmasking_gain (v3.78)               | > 0       | **121**   | ✓ |
| 4 | gate1_recovered (v3.80)                         | == true   | **true**  | ✓ |
| 5 | false_missing_claim_rate (v3.80)                | <= 0.20   | **0.00**  | ✓ |
| 6 | replay_stability (all sprints)                  | == 1.00   | **1.00**  | ✓ |

All six concept gates pass.

## Decision

**Redundancy Masking: BESTÄTIGT.** The v3.77 Neptun gate
#1 failure ("high_coverage_removal <= redundant_
removal") is fully explained by exact-coverage
duplication: every high-coverage anchor in the v3.50
plateau cohort sits in a redundancy class of 8
exact duplicates. Single-anchor removal cannot
unmask the missing claim because the doppelgänger
covers the same leakages. Removing the entire
redundancy class produces the expected 121-leakage
perturbation.

Per directive: redundancy masking is the mechanism.
Neptun's invisibility was not absence of signal but
suppression of signal by an epistemic doppelgänger.

DESi's answer to the directive's closing question
"War Neptun unsichtbar, weil ein epistemischer
Doppelgänger seine Bahnwirkung kompensierte?": **ja,
empirisch bestätigt.** All 8 anchors in the high-
coverage redundancy class are mutually
doppelgänger-equivalent — their coverage sets are
bit-identical. Removing one keeps the perturbation
hidden; removing all eight together reveals the
full 121-leakage perturbation.

## Sources

* `artifacts/v3_78/report.json`                              — redundant pair removal
* `artifacts/v3_78/redundant_pair_removal.json`              — 4 condition outcomes
* `artifacts/v3_79/report.json`                              — redundancy class census
* `artifacts/v3_79/redundancy_class_census.json`             — 3 classes + overlap matrix
* `artifacts/v3_80/report.json`                              — redundancy-aware Neptun
* `artifacts/v3_80/redundancy_aware_neptun.json`             — class removal + localization
* `artifacts/v3_80/redundancy_masking_claims.json`           — per-class masking claims

## Findings the documentation must encode

### 1. Redundant pair removal unmasks the perturbation (v3.78)

| Condition           | Removed                       | Loss | Magnitude |
|---------------------|-------------------------------|------|-----------|
| A_single_high_a     | v23:R5_04                     | 0    | 0         |
| B_single_high_b     | v314:D02                      | 0    | 0         |
| C_double_high_pair  | v23:R5_04 + v314:D02          | 121  | 121       |
| D_unrelated_pair    | v23:R5_02 + v317:R5_02        | 12   | 12        |

* Single-anchor removal of either high-coverage
  doppelgänger: 0 perturbation (the other covers
  the same 121 leakages).
* Removing BOTH simultaneously: 121 leakages
  uncovered.
* Unrelated 12-coverage pair: 12 leakages
  uncovered (same mechanism at smaller scale).
* `redundancy_unmasking_gain` = 121 (double minus
  max single).

### 2. The corpus has 3 exact-duplicate redundancy classes (v3.79)

| Class | Coverage Size | Members | Sample |
|-------|---------------|---------|--------|
| 0     | 121           | 8       | v23:R5_04, v314:D02, v314:D05, v315:G10, ... |
| 1     | 12            | 8       | v23:R5_02..R5_06, v317:R5_02..R5_06 |
| 2     | 0             | 4       | v23:R4_04, v314:C02, v317-h:C02, v317:R4_04 |

* `redundancy_class_count` = 3
* `exact_duplicate_count` = 3 (every class has
  >= 2 members)
* `partial_overlap_count` = 0 (the three classes
  are pairwise disjoint in coverage)
* `largest_redundancy_class` = 8 (Classes 0 and 1
  tie)

The entire 20-anchor plateau cohort decomposes into
just three exact-coverage groups; no anchor has
unique coverage.

### 3. Class-level removal recovers Neptun gate #1 (v3.80)

| Class | Members | Class Removal | Single Removal |
|-------|---------|---------------|----------------|
| 0 (high)   | 8 | 121           | 0              |
| 1 (bridge) | 8 | 12            | 0              |
| 2 (zero)   | 4 | 0             | 0              |

* `redundancy_aware_high_removal` = 121
* `redundancy_aware_redundant_removal` = 0
* `gate1_recovered` = `true` (121 > 0)
* `localization_accuracy` = 1.00 (both eligible
  class removals correctly localized to their own
  centroid; Class 2 has no orphan signal as
  expected for the zero-coverage class)
* `candidate_match_score` = 1.00
* `false_missing_claim_rate` = 0.00 (inherits
  v3.77's negative-control rejection)

Removing entire redundancy classes produces the
expected perturbation magnitudes. The v3.77 Neptun
gate failure was a single-anchor-removal artifact;
class-level removal restores the directive's
ordering high > redundant.

## What this confirms (and does not)

* CONFIRMED: the Neptun mechanism (inferring missing
  claims from perturbations) works when the
  REMOVAL UNIT is the redundancy class, not a
  single claim. The doppelgänger problem is real
  and resolvable.
* CONFIRMED: the v3.50 plateau cohort's redundancy
  structure is full and clean (3 classes, all exact-
  duplicate, all pairwise disjoint).
* NOT EXTENDED: redundancy masking outside the v3.50
  cohort is not measured here. Other claim spaces
  may show partial overlap rather than exact
  duplication.
* NOT CHANGED: Paper 11's exploratory status. The
  directive's opening "Kein Paper" is respected.

## Stop rules not triggered

* v3.78 `single_removal_perturbation` (= 0) PASS.
* v3.78 `double_removal_perturbation` (= 121) > 0.
* v3.78 `redundancy_unmasking_gain` (= 121) > 0.
* v3.79 `replay_stability` (1.00) PASS.
* v3.80 `gate1_recovered` (= true) PASS.
* v3.80 `false_missing_claim_rate` (= 0.00) <= 0.20.
* v3.78-v3.80 `replay_stability` (1.00) PASS.
