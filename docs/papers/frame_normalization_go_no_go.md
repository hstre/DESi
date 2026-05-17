# Frame-Normalization — Concept Gate Decision

**Status:** decision artifact for the Frame-
Normalization Doppelgänger Audit (v3.89–v3.92). Per
the opening directive ("Kein Paper", "Keine Synthese
bis v3.92") this document records ONLY the Concept
Gate result; no paper change, no new failure
category, no theory.

## Hypothesis

> Doppelgänger-Struktur existiert auch in Novel
> Families, wird aber durch Frame-Geometrie
> überlagert.

## Concept Gate evaluation

| # | Gate                                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | purity_no_frame > purity_full (v3.89)             | >         | **0.605 > 0.289** | ✓ |
| 2 | normalized_cluster_purity (v3.90)                 | >= 0.70   | **0.605**         | ✗ |
| 3 | normalized_proxy_accuracy (v3.91)                 | >= 0.70   | **0.605**         | ✗ |
| 4 | frame_normalized_auc (v3.92)                      | >= 0.70   | **0.712**         | ✓ |
| 5 | replay_stability (all four sprints)               | == 1.00   | **1.000**         | ✓ |

Three of five gates pass; gates 2 and 3 fail.

## Decision

**Frames erklären den Fail nicht vollständig.** Per
the directive's exact wording — "Wenn eines
scheitert: Frames erklären den Fail nicht
ausreichend." — the failure of gates 2 and 3 keeps
the frame-normalization hypothesis at the "partial
explanation" status. The audit records:

* `frame_id` is the dominant variance component
  (v3.89: 65.2% of total variance) and removing it
  more than doubles cluster purity on novel
  material.
* After residual normalization, blind clustering
  produces two pure subclusters (8 anchors all
  A_v315, 5 anchors all D_v314) but merges the
  remaining 25 anchors across three families
  (v3.90).
* The v3.82 minimal proxy
  ``{branch_cost, contradiction_load}`` is
  unchanged by frame normalization (v3.91:
  identical 0.605 purity with or without
  normalization) — it was already frame-
  independent.
* Pre-coverage forecasting on residual pairs
  achieves AUC 0.712 (v3.92), clearing the
  predictability gate. FPR drops from 0.811
  (v3.88) to 0.395; calibration error drops from
  0.569 to 0.373.

The frame-normalization hypothesis would require
all four discrimination gates (2, 3, 4) to pass.
Two fail. The hypothesis is therefore not raised
to "frames erklären den Fail vollständig" status -
it remains "frames erklären einen Teil des Fails,
aber nicht alles".

## Findings the documentation must encode

### 1. frame_id dominates novel-anchor variance (v3.89)

Per-dim variance share over the 38 novel anchors:

| Dimension              | Variance | Share  |
|------------------------|----------|--------|
| frame_id               | 7.064    | 0.652  |
| novelty                | 2.469    | 0.228  |
| contradiction_load     | 0.831    | 0.077  |
| branch_cost            | 0.457    | 0.042  |
| anchor_density         | 0.011    | 0.001  |
| confidence/source_q./routing/support | 0.000 | 0.000 |

* `frame_id` carries 65.2% of total variance.
* Removing it lifts blind-cluster purity from
  0.289 (FULL) to 0.605 (NO_FRAME).
* `FRAME_ONLY` clustering yields the same partition
  as `FULL` (frame_id alone reproduces the v3.86
  failure mode).
* Per-cell linear-regression residuals give
  the same purity as plain zeroing (0.605), so
  the linear component is the only frame
  contribution that matters here.

### 2. Frame normalization recovers partial structure (v3.90)

Blind clustering on residual vectors:

| Metric                  | Value      | Gate           |
|-------------------------|------------|----------------|
| normalized_cluster_count | 3         | -              |
| normalized_cluster_sizes | (25, 8, 5) | -             |
| normalized_distance_gap  | 1.23      | -              |
| normalized_cluster_purity | 0.605    | < 0.70 ✗       |
| normalized_cluster_recall | 0.000    | < 0.70 ✗       |
| purity_delta vs baseline | +0.316    | -              |

* Two clusters are PURE:
  * 8 anchors, all A_v315
  * 5 anchors, all D_v314
* The third cluster (25 anchors) merges
  G_v316susp + E_v317h + 3 D_v314 + 3 A_v315 -
  the family boundary between G and E remains
  collapsed.
* No cluster matches a family exactly →
  cluster_recall = 0.

### 3. The v3.82 proxy is not frame-hidden (v3.91)

| Metric                       | Value       | Gate         |
|------------------------------|-------------|--------------|
| raw_proxy_accuracy           | 0.605       | -            |
| normalized_proxy_accuracy    | 0.605       | < 0.70 ✗     |
| normalized_predictive_auc    | 0.712       | -            |
| best_minimal_feature_set     | (branch_cost, contradiction_load) | - |
| marginal_frame_gain          | +0.316      | -            |

* Proxy purity is identical on raw and residual
  vectors → the proxy was already frame-
  independent.
* Backward search over the informative-dim
  taxonomy converges on the same 2-feature set
  as v3.82.
* `marginal_frame_gain` records the boost that
  frame removal gives the FULL space (the proxy
  doesn't see it).

### 4. Pairwise forecasting passes after normalization (v3.92)

| Metric                  | Raw (v3.88) | Normalized | Δ      |
|-------------------------|-------------|------------|--------|
| predictive_auc          | 0.649       | 0.712      | +0.063 |
| forecast_margin         | -10.25      | -2.31      | +7.94  |
| false_positive_rate     | 0.811       | 0.395      | -0.416 |
| calibration_error       | 0.569       | 0.373      | -0.196 |

* AUC clears the 0.70 universality gate after
  normalization.
* Forecast margin remains negative (overlapping
  distributions), but the overlap shrinks
  substantially.
* FPR halves; calibration improves by ~35%.

## Why this is PARTIAL EXPLANATION, not COMPLETE

The directive's four discrimination gates (1, 2,
3, 4) split into:

* **Pass:** gate 1 (purity_no_frame beats full)
  and gate 4 (frame_normalized_auc clears 0.70).
* **Fail:** gate 2 (normalized_cluster_purity)
  and gate 3 (normalized_proxy_accuracy).

The purity-based gates fail at exactly 0.605
because the residual cluster sizes are (25, 8, 5)
- two clusters are pure but the giant 25-anchor
cluster still mixes three families. Frame removal
helps a lot but does not resolve the G_v316susp /
E_v317h merge.

The predictive gate (4) passes because pairwise
AUC integrates over all pair distances, and frame
removal sharpens the same-family vs. cross-family
score distribution overall - even though it does
not produce a hard cluster boundary between G and
E.

DESi's answer to the directive's closing question
"Verdeckt der Frame die Doppelgänger — oder gibt es
dort wirklich keine stabile Degeneracy?":
**Der Frame verdeckt einen Teil der Doppelgänger
(A_v315 und D_v314), aber zwischen G_v316susp und
E_v317h existiert keine vom Frame trennbare
Geometrie.** Two families' doppelgänger structure
emerges cleanly after frame normalization; two
others remain entangled with each other.

## What the documentation must NOT claim

* That frame_id is the only noise dimension.
  Anchor density (variance 0.011), confidence,
  source_quality, routing_state, support_state all
  carry zero variance on novel anchors; they
  cannot be noise sources because they are
  constant.
* That frame normalization solves the degeneracy
  question. Two of four discrimination gates
  still fail; G_v316susp and E_v317h remain
  merged in the residual clustering.
* That the v3.82 proxy was frame-hidden. The
  proxy is identical on raw and residual data
  (v3.91 normalized_proxy_accuracy ==
  raw_proxy_accuracy == 0.605).
* That the v3.85-v3.88 sprint's `corpus-specific`
  decision is overturned. The frame-normalized
  AUC pass (0.712) is one additional pass; the
  cluster-purity gates still fail.
* That a new failure category is introduced. The
  directive explicitly forbids new failure
  categories in this sprint.

## Stop rules and gate signals

* v3.89 condition #1 (`purity_no_frame >
  purity_full`) PASS. Documented.
* v3.90 condition #2 (`normalized_cluster_purity
  >= 0.70`) FAIL. Documented.
* v3.91 condition #3 (`normalized_proxy_accuracy
  >= 0.70`) FAIL. Documented.
* v3.92 condition #4 (`frame_normalized_auc >=
  0.70`) PASS. Documented.
* v3.89-v3.92 `replay_stability` (1.00) PASS.

## Sources

* `artifacts/v3_89/report.json`                              — frame contribution audit
* `artifacts/v3_89/frame_contribution_audit.json`           — 4 conditions, per-dim variance
* `artifacts/v3_90/report.json`                              — frame-normalized clustering
* `artifacts/v3_90/frame_normalized_clusters.json`          — 3 residual clusters + 703 distances
* `artifacts/v3_91/report.json`                              — frame-normalized minimal features
* `artifacts/v3_91/frame_normalized_minimal_features.json`  — 7 subset outcomes
* `artifacts/v3_92/report.json`                              — frame-normalized prediction
* `artifacts/v3_92/frame_normalized_prediction.json`        — 703 pair forecasts + calibration
