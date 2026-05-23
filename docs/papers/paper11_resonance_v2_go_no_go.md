# Paper 11 — Resonance v2 Go / No-Go Decision

**Status:** decision artifact for the Content–Method
Resonance Separation Sprint (v3.57–v3.60). The
directive's "Paper 11 bleibt pausiert" is respected:
this document records the v2 decomposition result, not
the paper.

## Concept Gate evaluation (directive § "Concept Gate")

| # | Gate                                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | decomposition_replay_stability (v3.57)            | == 1.00   | **1.00**  | ✓ |
| 2 | content_method_overlap (v3.57)                    | < 0.70    | **0.994** | ✗ |
| 3 | method OR content OR crossed transfer_rate (v3.58/59/60) | > 0       | **0 / 0 / 0** | ✗ |
| 4 | control_pairs remain near 0                       | near 0    | **0**     | ✓ |
| 5 | replay_stability (all sprints)                    | == 1.00   | **1.00**  | ✓ |

Three of five Concept Gates pass; gates #2 and #3
fail.

## Decision

**Paper 11: NO-GO (resonance v2).**

Per the directive's exact wording — "Wenn alles 0
bleibt: Pair resonance bleibt falsifiziert." — every
non-trivial transfer rate is 0:
``method_pair_transfer_rate = 0`` (v3.58),
``content_pair_transfer_rate = 0`` (v3.59),
``crossed_transfer_rate = 0`` (v3.60). The pair
resonance phenomenon is not recoverable by isolating
content features or method features or by any of the
four content × method conditions.

Paper 11 remains paused. The v3.50 resonance
phenomenon stands as a v3-aggregate finding only, not
a corpus-invariant property.

## Sources

* `artifacts/v3_57/report.json`                       — decomposition
* `artifacts/v3_57/content_method_decomposition.json` — 165 per-trajectory rows
* `artifacts/v3_58/report.json`                       — method-only resonance
* `artifacts/v3_58/method_resonance.json`             — global + per-corpus summaries
* `artifacts/v3_59/report.json`                       — content-only resonance
* `artifacts/v3_59/content_resonance.json`            — global + per-corpus summaries
* `artifacts/v3_60/report.json`                       — crossed resonance
* `artifacts/v3_60/crossed_resonance.json`            — 4-condition cell counts

## Findings the paper must encode (when the gate
re-passes)

### 1. Content and method are not decomposable in
this corpus (v3.57)

* `content_dims` = (frame_id, novelty, anchor_density,
  contradiction_load, source_quality) — 5
* `method_dims` = (support_state, routing_state,
  branch_cost, confidence) — 4
* `content_cluster_count` = 12  (1-NN components in
  the 25-d content space)
* `method_cluster_count` = 5    (1-NN components in
  the 20-d method space)
* `content_method_overlap` = 0.994
* `within_cohort_overlap` = 0.992
* `decomposition_replay_stability` = 1.00
* Recommendation: `CONTENT_METHOD_PARTIAL_OVERLAP`

The two feature subspaces produce nearly identical
cluster partitions. Knowing a trajectory's content
cluster effectively determines its method cluster.
The directive's separation hypothesis fails at the
decomposition step: the v3.50 phenomenon cannot be
explained by either subspace alone because the two
subspaces are entangled in this corpus.

### 2. Method-only resonance is global, not local (v3.58)

* `method_pair_resonance` (global) = 96 (vs v3.50's
  64 in full 9-d)
* `method_control_pairs` (global) = 0
* `method_subadditivity_score` = 0.283
* `method_pair_transfer_rate` = 0.00
* Per-corpus v23, v314: 0 resonant pairs each
* Recommendation: `METHOD_RESONANCE_GLOBAL_ONLY`

Method-only resonance is STRONGER globally than the
full-feature v3.50 result (96 vs 64 resonant pairs in
the same 20-anchor universe), but disappears
completely when probed per corpus. The pattern matches
v3.54: resonance is a cross-corpus aggregation effect.
Restricting to method features amplified the global
signal but left the per-corpus failure unchanged.

### 3. Content-only resonance is weaker AND still local (v3.59)

* `content_pair_resonance` (global) = 8
* `content_control_pairs` (global) = 0
* `content_subadditivity_score` = 0.035
* `content_pair_transfer_rate` = 0.00
* Per-corpus v23, v314: 0 resonant pairs each
* Recommendation: `CONTENT_RESONANCE_GLOBAL_ONLY`

Content-only resonance is much weaker than method-
only (8 vs 96 resonant pairs at their respective
discrimination radii). The bulk of the v3.50 signal
is carried by method-space; content adds only a
small residual.

### 4. Crossed test pinpoints the resonance cell (v3.60)

The factorial design:

| Condition           | pairs | resonant | rate  | mean_overlap |
|---------------------|-------|----------|-------|--------------|
| same_c / same_m     | 14    | 0        | 0.00  | 41.4         |
| same_c / diff_m     | 0     | 0        | 0.00  | 0.0          |
| diff_c / same_m     | 80    | 0        | 0.00  | 39.3         |
| **diff_c / diff_m** | **96** | **64**  | **0.667** | 0.0      |

* `resonance_by_condition` shows ALL 64 v3.50
  resonant pairs sit in the `diff_content /
  diff_method` cell
* `interaction_effect` = 0.00 (both same-c-cells and
  same-m-cells have rate 0)
* `crossed_transfer_rate` = 0.00 (within any corpus,
  anchors share both content and method)
* `best_explanation_model` = `INTERACTION_NEGATIVE`
* Recommendation: `CROSSED_RESONANCE_GLOBAL_ONLY`

100% of the v3.50 resonance lives in the cell where
both content AND method differ between paired
anchors. Resonance is therefore not content-driven,
not method-driven, and not coupling-driven (in the
sense of same_c/same_m). It is the geometric
signature of CROSS-CORPUS HETEROGENEITY: anchors from
different generative corpora cover complementary
leakage subsets.

## Why this is NO-GO, not partial-GO

The directive's gate uses AND across all five
conditions, and the catch-all rule "Wenn alles 0
bleibt: Pair resonance bleibt falsifiziert" triggers
when every transfer rate is 0. Both conditions are
satisfied:

* Gate #2 fails because content and method are
  entangled in this corpus — the decomposition
  produces non-distinct clusterings.
* Gate #3 fails because none of method-only, content-
  only, or crossed analyses produces a per-corpus
  transfer.

The v3.60 finding (resonance lives in the diff_c /
diff_m cell) is the structural answer to "what was
the v3.50 resonance?". It is the geometric
signature of mixing four different corpora, NOT a
discovered coupling mechanism. The phenomenon is
real (96 method-only resonant pairs at r=2.5 is
strong) but it is a property of the cross-corpus
aggregate, not of any single corpus or any single
feature subspace.

## What the next sprint may explore (out of scope
for this document)

1. **Within-corpus enrichment.** Per-corpus anchor
   counts are 6/3/1/1 (v23/v314/v315/v316). v315 and
   v316 are single-anchor corpora, ineligible for any
   pair test. A future sprint could probe whether
   additional plateau anchors exist in these corpora
   that v3.31's classifier missed.
2. **Cross-corpus as the deliberate construction.**
   The v3.60 finding can be reframed: "resonance is
   the structural signature of cross-corpus
   complementarity." A paper could be written about
   the diff_c/diff_m cell as the locus of inter-
   corpus information, rather than about "semantic
   coupling".
3. **Feature space at different scales.** The current
   decomposition uses the raw 9-d state vectors. A
   future sprint could probe whether normalising,
   re-weighting, or projecting the dimensions
   produces a separable content/method partition that
   v3.57 misses.
4. **Within-corpus discrimination probe.** Within v23
   (6 anchors), the same_c/same_m cell shows mean
   overlap 41.4 — meaningful set sharing but not
   resonance. A future sprint could ask why these
   pairs share leakage support without being
   classified as resonant.

## Stop rules not triggered (and the two that were)

* v3.57 `decomposition_replay_stability` (1.00) PASS.
* v3.57 `content_method_overlap` (0.994)
  **FAIL** — content and method are not
  decomposable in this corpus.
* v3.58 `replay_stability` (1.00) PASS.
* v3.58 `method_pair_transfer_rate` (0.00)
  contributes to gate #3 FAIL.
* v3.59 `replay_stability` (1.00) PASS.
* v3.59 `content_pair_transfer_rate` (0.00)
  contributes to gate #3 FAIL.
* v3.60 `replay_stability` (1.00) PASS.
* v3.60 `crossed_transfer_rate` (0.00)
  **FAIL** — gate #3 fails (all three
  transfer rates are 0).
