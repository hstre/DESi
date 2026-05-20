# Epistemic Doppelganger Probe — Concept Gate Decision

**Status:** decision artifact for the Epistemic
Doppelganger Probe Sprint (v3.81-v3.84). Per the
directive's "Kein Paper. Keine Synthese bis v3.84.
Nur Artefakte. Nur prüfen. Nicht übernehmen.",
this document records ONLY the concept-gate
result.

## Concept Gate evaluation (6 conditions)

| # | Gate                                       | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | cluster_purity (v3.81)                     | >= 0.70   | **1.00**  | ✓ |
| 2 | minimal_cluster_accuracy (v3.82)           | >= 0.70   | **1.00**  | ✓ |
| 3 | proxy_score (v3.82)                        | >= 0.70   | **1.00**  | ✓ |
| 4 | transfer_accuracy (v3.83)                  | >= 0.70   | **1.00**  | ✓ |
| 5 | predictive_auc (v3.84)                     | >= 0.70   | **1.00**  | ✓ |
| 6 | replay_stability (all sprints)             | == 1.00   | **1.00**  | ✓ |

All six gates pass.

## Decision

**Epistemic-Doppelganger-Hypothese: BESTÄTIGT.**

Per the directive's "Wenn alle sechs passen:
Doppelganger-Hypothese bestätigt. Dokumentieren,
nicht ins Framework übernehmen." the audit records
the empirical result. The hypothesis is supported;
no production-framework change follows from this
sprint.

## Killerfragen — beantwortet

1. **"Sieht DESi Doppelganger ohne Ablation?"**
   Yes. v3.81 blind single-link clustering of the
   20 plateau-anchor trajectory tail vectors
   recovers exactly 3 clusters of sizes 8/8/4 that
   match the v3.79 redundancy class map at
   purity=1.00 and recall=1.00 - with the cluster
   threshold chosen blindly from the data
   (largest-gap midpoint), not from labels.

2. **"Reicht eine Minimal-Feature-Teilmenge?"**
   Yes. v3.82 closed 6-condition ablation +
   greedy backward elimination identifies the
   set ``{branch_cost, contradiction_load}`` -
   2 of 9 state dimensions - as a perfect proxy
   (minimal_cluster_accuracy = 1.00,
   proxy_score = 1.00). Dropping branch_cost
   alone collapses purity to 0.60; dropping
   contradiction_load alone collapses purity to
   0.80. The other 7 dimensions are either
   zero-variance constants on plateau anchors
   (frame_id, source_quality, confidence,
   support_state, routing_state) or
   non-discriminative (anchor_density, novelty).

3. **"Transferieren Doppelganger zwischen
   Corpora?"**
   Yes. v3.83 joint blind clustering of the 11
   plateau anchors from the four closed reference
   corpora (v23, v314, v315, v316) recovers 3
   clusters that match the v3.79 redundancy
   classes restricted to those corpora. Two of
   the three joint clusters span 2+ corpora
   (cross_corpus_classes = 2): class 0 spans 4
   corpora, class 2 spans 2 corpora. All 10
   cross-corpus v3.79 pairs are recovered
   (transfer_accuracy = 1.00). Per-corpus
   clusterings are a refinement of the joint
   clustering (class_stability = 1.00).

4. **"Lassen sich Doppelganger vor-coverage
   vorhersagen?"**
   Yes. v3.84 pairwise forecast from
   ``score = -euclidean(tail(A), tail(B))``
   separates the 62 same-class pairs from the
   128 cross-class pairs perfectly
   (predictive_auc = 1.00,
   false_positive_rate at optimal threshold =
   0.00, forecast_margin = 1.72). Min-max
   binned calibration error is 0.17
   (<= 0.20 ceiling). No coverage computation
   is performed by the forecast - only the
   pre-coverage 45-d trajectory tail vector.

## Findings the documentation must encode

### 1. Blind clustering recovers v3.79 (v3.81)

Largest-gap-midpoint threshold on the
20-anchor x 20-anchor pairwise tail-vector
distance matrix is **1.376**. There are 62
within-class pairs ≤ 0.52 and 128 cross-class
pairs ≥ 2.24 - a bimodal distribution with a
single dominant gap of 1.72. Single-link
clustering at threshold 1.376 yields exactly the
three v3.79 classes.

| Blind cluster | Members                                                                                         | Matches v3.79 class |
|---------------|-------------------------------------------------------------------------------------------------|---------------------|
| 0             | v23:R5_02..06, v317:R5_02..06 (8)                                                              | Class 1 (cov 12)    |
| 1             | v23:R5_04, v314:D02, v314:D05, v315:G10, v316-susp:G10, v317-h:D02, v317-h:D05, v317:R5_04 (8) | Class 0 (cov 121)   |
| 2             | v23:R4_04, v314:C02, v317-h:C02, v317:R4_04 (4)                                                | Class 2 (cov 0)     |

### 2. Two dimensions suffice (v3.82)

Ablation outcomes (single-dim drop) sorted by
importance:

| Drop                | Importance | Purity after drop |
|---------------------|-----------:|------------------:|
| branch_cost         |       0.40 |              0.60 |
| contradiction_load  |       0.20 |              0.80 |
| anchor_density      |       0.00 |              1.00 |
| frame_id (control)  |       0.00 |              1.00 |
| novelty             |       0.00 |              1.00 |
| source_quality (ctl)|       0.00 |              1.00 |

Backward greedy elimination over all 9 dims
yields the minimal set ``{branch_cost,
contradiction_load}`` (2/9 dims). The clustering
on those 2 dims alone is identical to the
clustering on all 9.

### 3. Doppelganger classes span corpora (v3.83)

| Corpus | Anchors | Clusters | Sizes |
|--------|--------:|---------:|------:|
| v23    |       6 |        3 | 4/1/1 |
| v314   |       3 |        2 |   2/1 |
| v315   |       1 |        1 |     1 |
| v316   |       1 |        1 |     1 |

Joint clustering of all 11 anchors: 3 clusters
of sizes 5/4/2. Cluster 0 (cov 121) draws members
from v23, v314, v315, v316 - all four reference
corpora. Cluster 2 (cov 0) draws members from
v23 and v314.

### 4. Pre-coverage forecast separates pairs (v3.84)

The pairwise score ``-euclidean(tail(A), tail(B))``
on the 190 plateau-anchor pairs:

* AUC = 1.00 (perfect ranking, no ties)
* Optimal threshold = -1.376 (= midpoint of the
  bimodal score distribution, which equals the
  v3.81 cluster threshold by construction)
* FPR at optimal = 0.00
* Forecast margin = 1.72 (smallest same-class
  score minus largest cross-class score)
* Expected Calibration Error over 5 equal-width
  bins of normalised score = 0.17 (≤ 0.20)

## What this audit does NOT establish

* That DESi can detect doppelgangers in any
  unseen corpus. The four reference corpora used
  in v3.83 are exactly the directive-named
  closed set; transfer was perfect within that
  set but says nothing about novel corpora.
* That ``{branch_cost, contradiction_load}`` is
  the minimal-feature set for any other
  clustering task. The minimality is specific to
  v3.81's blind-equivalence clustering on
  plateau anchors in the v3.50 plateau cohort.
* That predictive AUC = 1.00 means doppelganger
  status is fundamentally pre-coverage-knowable.
  The plateau-anchor trajectories already encode
  the determinism that makes equal-coverage
  equal-trajectory; this is an artefact of the
  v3.50 plateau construction rather than a
  property of all DESi corpora.

## Sources

* ``artifacts/v3_81/report.json``                          - blind equivalence detection
* ``artifacts/v3_81/blind_equivalence_clusters.json``      - 3 clusters, 190 pairwise distances
* ``artifacts/v3_82/report.json``                          - minimal feature detection
* ``artifacts/v3_82/minimal_feature_detection.json``       - 6 ablations + importance + minimal set
* ``artifacts/v3_83/report.json``                          - cross-corpus doppelganger
* ``artifacts/v3_83/cross_corpus_doppelgaenger.json``      - per-corpus + joint clusterings
* ``artifacts/v3_84/report.json``                          - predictive degeneracy
* ``artifacts/v3_84/predictive_degeneracy.json``           - pairwise forecasts + calibration bins
