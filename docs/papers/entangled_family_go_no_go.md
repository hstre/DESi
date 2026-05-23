# Entangled Family Audit — Concept Gate Decision

**Status:** decision artifact for the Entangled
Family Audit (v3.93–v3.96). Per the opening
directive ("Kein Paper", "Keine Synthese bis
v3.96") this document records ONLY the Concept
Gate result; no paper change, no new failure
category, no theory.

## Question

> Sind diese beiden Familien echte epistemische
> Doppelgänger — oder fehlt uns eine weitere
> Trennungsdimension?

Entangled pair: **G_v316susp** (9 anchors) and
**E_v317h** (10 anchors) from the v3.85 novel
family pool.

## Concept Gate evaluation

| # | Gate                                              | Threshold | Measured       | Pass |
|---|---|---|---|---|
| 1 | dominant_dims gefunden (v3.93)                    | non-empty | (anchor_density, branch_cost) | ✓ |
| 2 | best_purity (v3.94 / v3.96)                       | >= 0.70   | **0.526**         | ✗ |
| 3 | resolved_auc (v3.96)                              | >= 0.70   | **0.506**         | ✗ |
| 4 | resolved_fpr < frame_normalized_fpr               | <         | **0.467 > 0.395** | ✗ |
| 5 | replay_stability (all four sprints)               | == 1.00   | **1.000**         | ✓ |

Two of five gates pass; gates 2, 3, and 4 fail.

## Decision

**Familien bleiben echte Doppelgänger.** Per the
directive's exact wording — "Wenn eines scheitert:
Familien bleiben echte Doppelgänger." — the failure
of gates 2, 3, and 4 keeps the entangled pair at
the "true doppelganger" status. The audit records:

* The residual variance left after frame
  normalization (0.014 total) is concentrated in
  `anchor_density` (79.2%) and `branch_cost`
  (18.7%) (v3.93).
* The candidate hidden dimensions exist, but the
  between-family mean differences are tiny
  (`branch_cost` 0.040, `anchor_density` 0.030)
  and within-family variance dominates - the
  signal is below the noise floor.
* No subset of 1, 2, or 3 state dimensions can
  separate G and E in the residual space (v3.94:
  129 subsets, zero beat the 0.526 majority-class
  baseline).
* G and E share the exact same temporal method
  signature - both rise on frame_id at state 2,
  novelty at state 1, branch_cost at state 1,
  confidence at state 2, support_state at state 4
  (v3.95: method_overlap = 1.0, path_distance = 0).
* Augmenting the residual space with temporal
  features (348 candidate FeatureSpecs in v3.96)
  cannot lift resolved_purity above 0.526 or
  resolved_auc above 0.506.

The Hidden-Dimension hypothesis would require
gates 2, 3, and 4 to pass. They do not. The pair
is therefore not "merely entangled by a missing
feature" - it is a genuine epistemic doppelganger
in DESi's state-vector representation.

## Findings the documentation must encode

### 1. Residual variance is tiny and proxy-disjoint (v3.93)

After frame normalization, only three dimensions
carry any residual variance over the 19 entangled
anchors:

| Dimension              | Variance | Share  |
|------------------------|----------|--------|
| anchor_density         | 0.01107  | 0.792  |
| branch_cost            | 0.00262  | 0.187  |
| contradiction_load     | 0.00029  | 0.021  |
| (other six dims)       | 0.0      | 0.000  |

* Total residual variance: 0.014.
* `anchor_density` is OUTSIDE the v3.82 proxy ⇒
  `proxy_information_loss` = 0.792.
* Between-family mean-diff sums are equally small:
  `branch_cost` 0.040, `anchor_density` 0.030,
  `contradiction_load` 0.013, others zero. A
  hypothetical "Trennungsdimension" should
  produce a mean-diff at least an order of
  magnitude larger.

### 2. Exhaustive ablation finds no separator (v3.94)

Closed search over every 1, 2, and 3-dim subset:

| Metric                       | Value     | Gate           |
|------------------------------|-----------|----------------|
| subset_count                 | 129       | -              |
| baseline_purity              | 0.526     | -              |
| best_dim_set                 | (support_state,) | (any subset ties) |
| best_purity                  | 0.526     | < 0.70 ✗       |
| dimensionality_cost          | 1         | -              |
| stability                    | 1.000     | (full degeneracy) |
| purity_above_baseline_count  | 0         | -              |

* Every subset ties the majority-class baseline.
* `purity_above_baseline_count = 0` is the
  central finding: no state-vector projection
  separates the two families.

### 3. Temporal signatures are identical (v3.95)

| Family       | frame_id | nov. | bc | conf. | supp. | (others) |
|--------------|---------|------|----|-------|-------|----------|
| G_v316susp   | 2       | 1    | 1  | 2     | 4     | -1       |
| E_v317h      | 2       | 1    | 1  | 2     | 4     | -1       |

(`-1` = dim never rises across the 5-state
trajectory.)

* `method_overlap` = 1.00 (every dim's majority
  rise index agrees).
* `path_distance` = 0.
* `temporal_separability` = 0.494 (near random).
* Maximum per-member Hamming distance from the
  foreign family's majority signature: 1 (only
  v317-h:E01 deviates, and only on `frame_id`).

### 4. Augmented feature space still cannot separate (v3.96)

| Metric                  | Value     | Gate           |
|-------------------------|-----------|----------------|
| candidate_spec_count    | 348       | -              |
| resolved_purity         | 0.526     | < 0.70 ✗       |
| resolved_auc            | 0.506     | < 0.70 ✗       |
| resolved_fpr            | 0.467     | -              |
| baseline_auc (v3.92)    | 0.712     | -              |
| baseline_fpr (v3.92)    | 0.395     | -              |
| best_feature_set        | residual=(anchor_density,), temporal=() | - |

* Resolved AUC is essentially chance.
* Resolved FPR (0.467) is HIGHER than the v3.92
  frame-normalized FPR (0.395) - the augmented
  feature space adds noise without adding signal,
  so the FPR-reduction gate fails.
* Note that v3.92's FPR was measured over the
  full 38-anchor pool; the v3.96 FPR is measured
  over the 19-anchor entangled pair only - the
  two numbers describe different populations but
  the directive's gate compares them directly.

## Why this is TRUE-DOPPELGANGER, not HIDDEN-DIMENSION

The directive's four discrimination gates split
into:

* **Pass:** gate 1 (dominant dims exist - the
  residual has structure to audit).
* **Fail:** gates 2 (purity), 3 (AUC), 4 (FPR)
  all fail despite an exhaustive 348-spec search
  over augmented features.

The residual signal IS present (anchor_density
explains 79% of post-frame variance) but it does
not separate the two families. Within-family
variance on `anchor_density` is comparable to or
greater than the between-family mean difference,
so even an optimal linear classifier cannot push
purity above the 10/19 = 0.526 majority baseline.

DESi's answer to the directive's closing question
"Fehlt uns eine Dimension — oder sehen wir hier
echte family-übergreifende epistemische
Doppelgänger?":
**Wir sehen echte family-übergreifende
Doppelgänger.** G_v316susp and E_v317h occupy the
same point in DESi's joint (state-vector,
temporal-signature) representation. The semantic
content of the two text families is different -
G_v316susp contains circular-reasoning patterns
("X rests on Y. Y rests on X. Therefore...") and
E_v317h contains heldout natural-language
syllogisms - but DESi's representation does not
encode that distinction.

## What the documentation must NOT claim

* That G and E share semantic content. The text
  surface is obviously different (circular
  reasoning vs simple syllogisms); only DESi's
  state-vector representation collapses them.
* That an unobserved DESi dimension exists that
  would separate them. The closed StateVector
  enum has nine dimensions; the residual variance
  audit covers all nine.
* That this is a failure of the v3.85-v3.92
  pipeline. The pipeline correctly identified
  these two families as entangled in v3.86; the
  v3.93-v3.96 audit confirms the entanglement is
  intrinsic, not algorithmic.
* That all cross-family pairs in DESi are
  doppelgangers. Two of the four v3.85 novel
  families (A_v315, D_v314) DID separate cleanly
  in v3.90 after frame normalization.
* That a new failure category is introduced. The
  directive explicitly forbids new failure
  categories in this sprint.

## Stop rules and gate signals

* v3.93 dominant_dims found (anchor_density,
  branch_cost) PASS. Documented.
* v3.94 best_purity (0.526) FAIL. Documented.
* v3.95 method_overlap (1.0), path_distance (0)
  PASS the doppelganger-confirmation criterion;
  temporal_separability (0.494) FAILS the
  separability criterion. Documented.
* v3.96 resolved_purity (0.526), resolved_auc
  (0.506), resolved_fpr (0.467 > 0.395) all
  FAIL. Documented.
* v3.93-v3.96 replay_stability (1.00) PASS.

## Sources

* `artifacts/v3_93/report.json`                              — residual dimension audit
* `artifacts/v3_93/entangled_dimensions.json`                — per-dim variance and mean diffs
* `artifacts/v3_94/report.json`                              — exhaustive ablation
* `artifacts/v3_94/entangled_ablation.json`                  — 129 subset outcomes
* `artifacts/v3_95/report.json`                              — method signal audit
* `artifacts/v3_95/entangled_method_signal.json`             — per-member signatures
* `artifacts/v3_96/report.json`                              — entanglement resolution
* `artifacts/v3_96/entangled_resolution.json`                — 348 resolution outcomes
