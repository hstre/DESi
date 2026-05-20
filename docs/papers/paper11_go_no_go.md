# Paper 11 — Go / No-Go Decision

**Status:** decision artifact for the Semantic Field
Probe Sprint (v3.49–v3.52). The directive's opening
"Paper 11 noch nicht beginnen" is respected: this
document records that the Concept Gate is met and that
the field-coupling hypothesis is empirically supported,
but it does not constitute the paper itself.

## Concept Gate evaluation (directive § "Concept Gate")

| # | Gate                                          | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | radius_break survives frame masking (v3.49)   | True      | **True**  | ✓ |
| 2 | subadditivity_score (v3.50)                   | > 0       | **0.184** | ✓ |
| 3 | anti_anchor_effect (v3.51)                    | > 0       | **145**   | ✓ |
| 4 | discontinuity_score (v3.52)                   | > 0       | **0.910** | ✓ |
| 5 | replay_stability (all sprints)                | == 1.00   | **1.00**  | ✓ |

All five Concept Gates pass.

## Decision

**Concept Gate: PASS.** The v3.43–v3.45 field-leakage
phenomenon is not reducible to a `frame_id@2` proxy
(v3.49), exhibits pair-level resonance distinct from a
random control cohort (v3.50), admits clean local
suppression by anti-anchors drawn from the leakage
manifold (v3.51), and tips DISCRETELY with anchor count
rather than growing smoothly (v3.52).

The directive's framing question — "Bin ich nur ein
Frame-Proxy… oder sehe ich echte semantische
Feldkopplung?" — resolves to: **echte Kopplung** (real
coupling). The semantic field is empirically grounded
in geometric structure beyond any single dimension.

Paper 11 may be opened in a future sprint; this
document is the Concept Gate decision, not the paper.

## Sources

* `artifacts/v3_49/report.json`                — frame artifact audit
* `artifacts/v3_49/frame_artifact_audit.json`  — full mask x radius outcomes
* `artifacts/v3_50/report.json`                — pair resonance
* `artifacts/v3_50/pair_resonance_matrix.json` — 190 plateau + 190 control pairs + 200 triples
* `artifacts/v3_51/report.json`                — anti-anchor probe
* `artifacts/v3_51/anti_anchor_effects.json`   — 4 anti kinds x ~395 trajectories
* `artifacts/v3_52/report.json`                — phase transition
* `artifacts/v3_52/semantic_phase_curve.json`  — 7-point phase curve

## Findings the paper must encode

### 1. Frame is not the discriminator (v3.49)

Five closed masks were applied to the plateau anchors
and the test trajectories uniformly. Per-mask radius-
break evaluation (leakage at r=4.0 minus leakage at
r=2.0):

| Mask           | leak@r=4 | leak@r=2 | break? |
|----------------|----------|----------|--------|
| none           | 145      | 0        | YES    |
| frame_at_2     | 145      | 0        | YES    |
| frame_full     | 145      | 0        | YES    |
| frame_permuted | 139      | 0        | YES    |
| support_only   | 145      | 145      | NO     |
| geometry_only  | 145      | 0        | YES    |

* `radius_break_survives_frame_masking` = `true`
* `artifact_likelihood` = 0.20 (only `support_only`
  collapses across 5 non-identity masks)

Plateau and leakage trajectories share identical
frame_id traces (0,0,5,5,5 in 5-state corpus); masking
frame_id zeros a coordinate that was already equal
between the two groups, so Euclidean distance is
invariant. The discrimination is carried by
anchor_density, contradiction_load and the final-state
divergence.

### 2. Anchor pairs are resonant (v3.50)

At PROBE_RADIUS = 3.5 (the v3.43 discrimination band):

| Cohort  | pairs | resonant | subadditivity | mean union | max union |
|---------|-------|----------|---------------|------------|-----------|
| plateau | 190   | 64       | 0.184         | 86.8       | 133       |
| control | 190   | 0        | 0.464         | 131.7      | 133       |

* `resonance_gap` = 64 (plateau - control)
* `triple_max_extra` = 0 (triples never add anything
  beyond the best pair union; the field is fully
  pair-determined in this corpus)

Plateau pairs are MORE complementary than random
control pairs from the same corpus. The 64 resonant
plateau pairs (neither coverage is a subset of the
other) are absent in the random control cohort entirely.

### 3. Anti-anchors locally suppress the field (v3.51)

PLATEAU_RADIUS = 4.0, ANTI_RADIUS = 2.5, ANTI_COUNT = 5:

| Anti kind        | leakage | plateau_recall | leakage_reduction |
|------------------|---------|----------------|-------------------|
| none (baseline)  | 145     | 1.00           | 0.00              |
| leakage_sample   | **0**   | **1.00**       | **1.00**          |
| rescued_sample   | 24      | 0.60           | 0.83              |
| plateau_sample   | 145     | 0.00           | 0.00              |

* `anti_anchor_effect` = 145 (full suppression)
* `repulsion_count` = 287 trajectories repelled
* `plateau_recall_at_best` = 1.00

Five leakage trajectories used as anti-anchors at
suppression radius 2.5 perfectly suppress all 145
leakage trajectories while leaving every plateau
resolution intact. The orthogonal control
(`rescued_sample`) suppresses some leakage but at the
cost of plateau recall, confirming that the leakage
manifold is geometrically distinct enough to admit a
clean local suppressor.

### 4. The phase transition is discrete (v3.52)

PROBE_RADIUS = 3.5; phase curve over the sweep
{0, 1, 2, 3, 4, 8, 20}:

| k  | leakage | additive | plateau_recall | coupling |
|----|---------|----------|----------------|----------|
| 0  | 0       | 0        | 0.00           | n/a      |
| 1  | 0       | 0        | 1.00           | n/a      |
| 2  | 12      | 12       | 1.00           | 0.000    |
| 3  | 12      | 24       | 1.00           | 0.500    |
| 4  | **133** | 145      | 1.00           | 0.083    |
| 8  | 133     | 290      | 1.00           | 0.541    |
| 20 | 133     | 1064     | 1.00           | 0.875    |

* `discontinuity_score` = 0.910 (the k=3 → k=4 jump
  contributes 121 of the 133-leakage maximum)
* `saturation_point` = 4 anchors
* `coupling_strength` = 0.724 (overall subadditivity)
* Recommendation: `PHASE_DISCRETE`

Leakage growth is not smooth: a single anchor addition
(at k=4) accounts for 91% of the asymptotic leakage.
The system "tips" rather than ramps.

## What the paper must NOT claim

* That the resonance structure generalises to other
  corpora. The v3.50 pair counts are pinned to the
  v23-family plateau anchors and may not survive
  cross-corpus replication.
* That `support_only` collapse is a frame-proxy
  finding. It is the opposite — collapsing the
  state vector to a single dimension trivially
  reduces discrimination regardless of which
  dimension survives.
* That anti-anchors work via repulsion in any
  physical sense. The mechanism is set-difference:
  the policy stops firing where it would otherwise.
  The "field" framing is a useful metaphor for the
  geometric structure, not a claim about underlying
  forces.
* That the discrete phase transition implies a
  control parameter. The "k" axis is anchor count,
  ordered by trajectory_id alphabetical; reordering
  would change the curve shape (though saturation
  and coupling_strength are order-invariant).
* That the saturation at k=4 means "4 claims are
  sufficient to define the field". The 4 specific
  anchors that saturate include the 121-coverage
  set ({v23:R5_04, ...}); choosing a different
  subset could shift the saturation point.

## Stop rules not triggered

* v3.49 `replay_stability` (1.00) meets the 1.0
  anchor.
* v3.49 `radius_break_survives_frame_masking`
  (`true`) meets Concept Gate #1.
* v3.50 `attribution_stability` (1.00) meets the
  1.0 anchor.
* v3.50 `plateau_summary.subadditivity_score`
  (0.184) is strictly positive; Concept Gate #2
  passes.
* v3.51 `suppression_stability` (1.00) meets the
  1.0 anchor.
* v3.51 `anti_anchor_effect` (145) is strictly
  positive; Concept Gate #3 passes.
* v3.52 `replay_stability` (1.00) meets the 1.0
  anchor.
* v3.52 `discontinuity_score` (0.91) is strictly
  positive; Concept Gate #4 passes.

## Next direction (out of scope for this document)

A future sprint may:

1. Replicate v3.50 on a held-out corpus (no v23
   trajectories used to seed the manifold) and check
   whether the resonance_gap survives.
2. Test whether anti-anchor suppression generalises
   to other failure manifolds (e.g. the v3.46 GAP
   cohort) - if leakage_sample anti-anchors also
   suppress GAP, the mechanism is generic; if not,
   each manifold needs its own anti-anchor
   construction.
3. Measure the phase curve at additional radii
   (3.0, 3.25, 3.75) to characterise the
   discontinuity envelope.
4. Investigate whether the 4 anchors that saturate
   at k=4 share a structural property
   distinguishing them from the 121-coverage and
   0-coverage anchors.
