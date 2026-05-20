# Epistemic Degeneracy — Structural Invariance Probe

**Status:** decision artifact for the Novel Claim
Family Doppelgänger Probe (v3.85–v3.88). Per the
opening directive ("Kein Paper", "Keine Synthese
bis v3.88") this document records ONLY the Concept
Gate result; no paper change, no new failure
category, no theory.

## Question

> Ist Epistemic Degeneracy ein echtes Strukturgesetz
> — oder nur auf bisher bekannten Claim-Familien
> sichtbar?

## Concept Gate evaluation

| # | Gate                                              | Threshold | Measured       | Pass |
|---|---|---|---|---|
| 1 | overlap_with_prior (v3.85)                        | == 0      | **0**          | ✓ |
| 2 | cluster_purity (v3.86)                            | >= 0.70   | **0.289**      | ✗ |
| 3 | cluster_recall (v3.86)                            | >= 0.70   | **0.000**      | ✗ |
| 4 | proxy_accuracy (v3.87)                            | >= 0.70   | **0.605**      | ✗ |
| 5 | predictive_auc (v3.88)                            | >= 0.70   | **0.649**      | ✗ |
| 6 | replay_stability (all four sprints)               | == 1.00   | **1.000**      | ✓ |

Two of six gates pass; gates 2, 3, 4, and 5 fail.

## Decision

**Epistemic Degeneracy bleibt corpus-spezifisch.**
Per the directive's exact wording — "Wenn eines
scheitert: Degeneracy bleibt corpus-spezifisch." —
the failure of gates 2, 3, 4, and 5 keeps the
structural-law hypothesis at the "corpus-specific"
status. The audit records:

* DESi can isolate genuinely new claim material
  (v3.85: four families, 38 anchors, zero overlap
  with any prior plateau/leakage/mozart/gap/bridge/
  resonance/redundancy sprint input).
* On that novel material, blind clustering does
  NOT recover family boundaries (v3.86: two
  clusters at sizes 34/4 instead of four clusters
  at sizes 11/8/10/9).
* The v3.82 minimal proxy
  ``{branch_cost, contradiction_load}`` does
  transfer in spirit (v3.87 proxy_gap = -0.316,
  proxy beats the full feature space), but does
  NOT cross the 0.70 universality threshold.
* Pre-coverage forecasting on novel pairs achieves
  AUC 0.649 (v3.88), above random but below the
  predictability threshold.

The structural-law hypothesis would require all
four discrimination gates (purity, recall, proxy,
AUC) to pass. They do not. The hypothesis is
therefore not raised to "structural law" status -
it remains "valid on the v3.79 plateau cohort, weak
on novel families in this corpus".

## Findings the documentation must encode

### 1. Family isolation succeeds without leakage (v3.85)

Four claim families selected with zero overlap
with any prior-sprint input:

| Family       | Corpus      | Letter | Members | Variance |
|--------------|-------------|--------|---------|----------|
| A_v315       | v315        | A      | 11      | 3.93     |
| D_v314       | v314        | D      | 8       | 3.51     |
| E_v317h      | v317-h      | E      | 10      | 2.08     |
| G_v316susp   | v316-susp   | G      | 9       | 0.13     |

* ``overlap_with_prior`` = 0 → stop rule does NOT
  trigger; sprint is valid.
* ``family_variance`` (mean) = 2.41 → every family
  carries non-trivial internal variation.
* Pairwise cross-family ``min_distance`` = 0 for
  every pair → doppelgänger candidates exist
  across family boundaries (the v3.86 hypothesis
  is at least testable).

### 2. Blind clustering does not recover novel families (v3.86)

Apply the v3.81 single-link / largest-gap
algorithm to the 38 novel anchors:

| Metric                     | Value     | Gate        |
|----------------------------|-----------|-------------|
| predicted_cluster_count    | 2         | -           |
| cluster_sizes              | (34, 4)   | -           |
| distance_gap               | 6.58      | -           |
| cluster_purity             | 0.289     | < 0.70 ✗    |
| cluster_recall             | 0.000     | < 0.70 ✗    |

* The largest gap in the pairwise distance list is
  3.16 → 10.0, which separates an outlier
  trajectory population (4 anchors) from
  everything else (34 anchors). The natural
  family-scale separation lives BELOW that gap
  and therefore never becomes the threshold.
* No single blind cluster matches a single family
  exactly → cluster_recall = 0.

### 3. The v3.82 proxy partially transfers (v3.87)

Using only ``branch_cost`` and
``contradiction_load``:

| Metric                | Value      | Gate        |
|-----------------------|------------|-------------|
| proxy_accuracy        | 0.605      | < 0.70 ✗    |
| baseline_full_purity  | 0.289      | -           |
| proxy_gap             | -0.316     | -           |
| feature_stability     | 0.605      | -           |

* ``proxy_gap`` is **negative**: the 2-feature
  proxy beats the full 9-dimensional space on
  novel material.
* The only dimension that meaningfully shifts
  purity when added to the proxy is ``frame_id``
  (delta -0.316) → ``frame_id`` is the dominant
  noise source on novel material; it was a
  zero-variance control on plateau.
* No new positively informative dimension emerges
  on novel families → branch_cost +
  contradiction_load remain the dominant signal,
  but they are not strong enough alone to clear
  0.70.

### 4. Pre-coverage forecasting yields weak signal (v3.88)

Pairwise forecast on 703 novel pairs (164 same-
family, 539 cross-family):

| Metric                     | Value     | Gate        |
|----------------------------|-----------|-------------|
| predictive_auc             | 0.649     | < 0.70 ✗    |
| forecast_margin            | -10.25    | -           |
| optimal_threshold          | -5.13     | -           |
| false_positive_rate @ opt  | 0.811     | -           |
| calibration_error          | 0.569     | -           |

* AUC is above the random-baseline of 0.5 but
  below the predictability threshold.
* ``forecast_margin`` strongly negative → positive
  and negative score distributions overlap
  heavily.
* ``false_positive_rate`` at the optimal threshold
  is 0.81 → 81% of cross-family pairs would be
  falsely flagged as doppelgängers; the forecast
  is unusable as a hard classifier on novel
  material.
* High ``calibration_error`` (0.57) confirms the
  raw negative-distance score is not a
  well-calibrated probability on novel families.

## Why this is CORPUS-SPECIFIC, not STRUCTURAL

The directive's four discrimination gates (2-5)
each fail on novel material:

* Gate 2 (purity) and gate 3 (recall): the
  family-scale signal that v3.81 recovered cleanly
  on the plateau cohort is dominated by an
  outlier-driven distance gap on novel anchors.
* Gate 4 (proxy): branch_cost + contradiction_load
  is still the dominant signal pair, but the
  underlying family separation is itself weak, so
  even a perfect-on-paper proxy cannot exceed the
  underlying separation.
* Gate 5 (forecast): the pairwise distance score
  inherits the same weak family separation; AUC
  reflects this.

DESi's answer to the directive's closing question
"Erkenne ich epistemische Doppelgänger auch dort,
wo ich noch nie gesucht habe?":
**Teilweise, aber nicht zuverlässig.** Doppelgänger
pairs exist in the novel families (``min_distance``
= 0 across every pair of families), but family
boundaries cease to be the dominant geometric
structure - distance reflects trajectory-length
outliers more than family identity.

## What the documentation must NOT claim

* That epistemic degeneracy is universal. The
  v3.86–v3.88 chain shows it is not, on this
  corpus's novel families.
* That degeneracy does not exist outside the
  plateau cohort. The v3.85 isolation and the
  v3.87 proxy_gap = -0.316 result both show that
  the same 2-feature subspace is still the
  dominant signal source on novel material; the
  signal is just weaker.
* That the v3.82 proxy must be revised. The proxy
  is preserved; v3.87 imports it from v3.82 and
  does not recompute it. The drop from 1.00
  (plateau) to 0.605 (novel) is a property of the
  novel families, not of the proxy.
* That a new failure category is introduced. The
  directive explicitly forbids new failure
  categories in this sprint.

## Stop rules and gate signals

* v3.85 ``overlap_with_prior`` (0) PASS. Sprint
  valid.
* v3.86 ``cluster_purity`` (0.289) and
  ``cluster_recall`` (0.000) FAIL. Documented.
* v3.87 ``proxy_accuracy`` (0.605) FAIL.
  Documented (proxy_gap = -0.316 noted as
  mitigating).
* v3.88 ``predictive_auc`` (0.649) FAIL.
  Documented (above 0.5 baseline).
* v3.85–v3.88 ``replay_stability`` (1.00) PASS.

## Sources

* `artifacts/v3_85/report.json`                              — family isolation
* `artifacts/v3_85/novel_claim_families.json`               — 4 families, 38 anchors
* `artifacts/v3_86/report.json`                              — blind clustering
* `artifacts/v3_86/novel_family_clusters.json`              — clusters + pairwise distances
* `artifacts/v3_87/report.json`                              — proxy transfer
* `artifacts/v3_87/novel_family_proxy.json`                 — proxy vs full clusterings
* `artifacts/v3_88/report.json`                              — predictive forecast
* `artifacts/v3_88/novel_family_predictive.json`            — 703 pair forecasts
