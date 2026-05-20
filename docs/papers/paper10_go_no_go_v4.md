# Paper 10 — Go / No-Go Decision v4

**Status:** decision artifact for the Field Leakage Audit
Sprint (v3.43–v3.45). Paper 10 v3 (conditional GO with
the full-corpus overcontrol caveat) is superseded by
this document.

## Gate evaluation (directive § "Paper-10 Gate v4")

| # | Gate                                  | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | explanation_replay_stability (v3.43)  | == 1.00   | **1.00**  | ✓ |
| 2 | optimal_radius exists (v3.44)         | exists    | **"0.25"** | ✓ |
| 3 | plateau_recall (v3.44)                | >= 0.90   | **1.00**  | ✓ |
| 4 | leakage_reduction (v3.44)             | >= 0.90   | **1.00**  | ✓ |
| 5 | attribution_stability (v3.45)         | == 1.00   | **1.00**  | ✓ |

All five named gates pass.

## Decision

**Paper 10: conditional GO with a domain-knowledge caveat
(see § "Why this is not unconditional GO").**

The named Paper-10 v4 gates all pass. Paper 10 may be
written if the caveat is included verbatim.

## Sources

* `artifacts/v3_43/report.json`                — leakage census
* `artifacts/v3_43/leakage_inventory.json`     — 145 LeakageCase
* `artifacts/v3_43/manifold_distance_map.json` — 145 × 20 distances
* `artifacts/v3_44/report.json`                — radius sweep
* `artifacts/v3_44/radius_sweep.json`          — per-outcome rows
* `artifacts/v3_45/report.json`                — mass interaction
* `artifacts/v3_45/claim_field_effects.json`   — per-mass outcomes
* `artifacts/v3_45/field_leakage_claims.json`  — 145 claims
* `artifacts/v3_37/report.json`                — v3.37 self-explanation
* `artifacts/v3_38/report.json`                — v3.38 separability
* `artifacts/v3_39/report.json`                — v3.39 specificity (caveat)

## Findings the paper must encode

### 1. The 145 leakage trajectories form their own manifold (v3.43)

* `leakage_count` = 145
* `mean_manifold_distance` = 2.989 (range 2.926..3.683)
* `leakage_cluster_count` = 3 (sizes 121, 12, 12)
* `nearest_neighbor_rate` = 0.00
* `same_frame_family_rate` = 1.00
* `same_support_family_rate` = 1.00
* `explanation_replay_stability` = 1.00
* Reason: every leakage case maps to
  `FRAME_FAMILY_AUDIT_WITHDRAWN`.

The 145 SUPPORTED non-plateau trajectories share the
plateau's pre-audit frame and support anchors but diverge
at the audit step. They sit ~3 units from the plateau
manifold in 45-d space and form three internal sub-
clusters.

### 2. A radius-bounded selector recovers specificity (v3.44)

Six closed radii were tested over the full corpus:

| r    | leakage_count | plateau_recall |
|------|---------------|----------------|
| 0.25 | 0             | 1.00           |
| 0.5  | 0             | 1.00           |
| 1.0  | 0             | 1.00           |
| 2.0  | 0             | 1.00           |
| 4.0  | 145           | 1.00           |
| inf  | 145           | 1.00           |

The leakage curve is a clean step function. Transition
happens between r = 2.0 and r = 4.0 (the v3.43
`min_manifold_distance` = 2.926). The
v3.39 single-feature selector is the `r = inf` case;
any finite radius below 2.926 fully separates the two
manifolds.

* `optimal_radius` = "0.25"
* `optimal_plateau_recall` = 1.00
* `optimal_leakage_count` = 0
* `optimal_leakage_reduction` = 1.00
* `largest_clean_radius` = "2"
* `radius_stability` = 1.00

### 3. The leakage field saturates at k=2 anchors (v3.45)

Probe radius = 4.0 (the smallest radius where leakage is
non-zero). Mass effect curve:

| k  | plateau_resolved | leakage |
|----|------------------|---------|
| 0  | 0                | 0       |
| 1  | 20               | 121     |
| 2  | 20               | 145     |
| 4  | 20               | 145     |
| 8  | 20               | 145     |
| 20 | 20               | 145     |

* `leakage_saturation` = 2 anchors
* `interference_count` = 10 (out of all (a, b) pairs
  with a + b <= 20)
* `repulsion_count` = 0
* `dominant_mass_claims` = `v23:R5_02`, `v23:R5_03`,
  `v23:R5_05`, `v23:R5_06`, `v317:R5_02`
* `attribution_stability` = 1.00

Two anchors are sufficient to capture the full leakage
set. The 1+1 union is strictly smaller than the
1+1 sum (121+121 vs 145), so the field is
subadditive (positive interference, no repulsion).
Five plateau anchors individually cover all 145 leakages
on their own — the "field" is concentrated, not
distributed.

## Why this is not unconditional GO

The `optimal_radius = 0.25` selector requires the
plateau anchor set to be known in advance — the
trajectories the policy is supposed to rescue must
already be identified as plateau. This is an audit-time
distinction (after the audit has fired and produced
`support_state = 2.0`). The selector is therefore a
**post-audit re-intervention**, not a pre-audit gate.

Concretely:

* v3.39's `frame_stability_condition` is pre-audit
  (reads `frame_id` at index n-2) but non-specific
  (`full_corpus_overcontrol = 145`).
* v3.44's radius-bounded selector is specific
  (`leakage = 0` at r = 0.25) but presumes the plateau
  anchor set is already labelled. The radius gate is
  computed against the SAME plateau cohort it is meant
  to rescue.

This is geometrically correct and operationally honest:
the v3.39 corpus does not admit a pre-audit predicate
that separates plateau from SUPPORTED, because their
pre-audit state vectors are identical at index n-2
(v3.43 finding: same_pre_audit_state rate measurable on
the inventory artifact).

The directive's `optimal_radius` gate is met. The
paper must state explicitly that this is a re-
intervention policy, not a forecasting predicate.

## What the paper must NOT claim

* That the radius-bounded selector "predicts" plateau
  cases. It selects by proximity to known plateau
  anchors; it does not generalise to unseen
  trajectories without their plateau label.
* That field leakage is universally subadditive. The
  v3.45 interaction is sub-additive in this corpus,
  but the directive lists only k ∈ {0,1,2,4,8,20} -
  the interference behaviour outside the closed mass
  set is not measured.
* That a saturation at k=2 anchors generalises beyond
  v23-family plateau structure. The v3.43 finding
  shows the leakage cohort is a v23 frame-family
  artifact; cross-corpus generalisation requires the
  v5-line probe lesson (re-audit).
* That the v3.39 policy was wrong. It was geometrically
  correct on the v3.35 cliff-class universe;
  v3.43-v3.45 only show that its EFFECTIVE RADIUS was
  too large for the broader corpus.

## Stop rules not triggered

* v3.43 `explanation_replay_stability` (1.00) meets
  the 1.0 anchor.
* v3.44 `optimal_radius` exists in the closed RADII
  set (smallest is "0.25").
* v3.44 `leakage_reduction` (1.00) exceeds the 0.90
  floor.
* v3.45 `attribution_stability` (1.00) meets the 1.0
  anchor.

## Next sprint suggestion (out of scope for this document)

A v3.46 sprint that tests the radius-bounded selector
on a held-out corpus (no v23 trajectories used to
seed the manifold) would close the "knowing the
plateau cohort in advance" gap. If the held-out
plateau-recall stays high under the same radius, the
field hypothesis generalises. If not, it is a v23
corpus artifact and the recommendation must move from
`FIELD_RADIUS_RECOVERED` to
`FIELD_RADIUS_LOCALLY_RECOVERED`.
