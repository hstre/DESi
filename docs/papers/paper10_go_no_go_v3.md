# Paper 10 — Go / No-Go Decision v3

**Status:** decision artifact for the Specificity Recovery
Sprint (v3.37–v3.39). Paper 10 v2 (NO-GO on specificity)
is superseded by this document.

## Gate evaluation (directive § "Paper-10 Gate v3")

| # | Gate                              | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | self_explained_count (v3.37)      | == 14     | **14**    | ✓ |
| 2 | unexplained_cases (v3.37)         | == 0      | **0**     | ✓ |
| 3 | separability (v3.38)              | >= 0.70   | **1.00**  | ✓ |
| 4 | specificity_score (v3.39)         | >= 0.90   | **1.00**  | ✓ |
| 5 | plateau_recall (v3.39)            | >= 0.90   | **1.00**  | ✓ |
| 6 | replay_stability (v3.39)          | == 1.00   | **1.00**  | ✓ |

All six named gates pass.

## Decision

**Paper 10: conditional GO with a corpus-wide caveat (see
§ "Why this is not unconditional GO").**

The named gates from the v3.39 directive all pass on the
v3.35-compatible universe. Paper 10 may be written if the
caveat is included verbatim.

## Sources

* `artifacts/v3_37/report.json`                        — self-explanation
* `artifacts/v3_37/self_explanation.json`              — 34 per-mover records
* `artifacts/v3_37/overgeneralized_stabilization_claims.json`
* `artifacts/v3_38/report.json`                        — separability
* `artifacts/v3_38/plateau_vs_accidental.json`         — 1-NN clusters
* `artifacts/v3_38/separability_map.json`              — 45-feature accuracy map
* `artifacts/v3_39/report.json`                        — specificity recovery
* `artifacts/v3_39/specificity_recovery.json`          — per-policy outcomes
* `artifacts/v3_35/report.json`                        — v3.35 baseline
* `artifacts/v3_36/report.json`                        — v3.36 noise/timing

## Findings the paper must encode

### 1. DESi can self-explain its accidental rescues (v3.37)

For each of the 14 unexpected rescues v3.35 surfaced:

* `decisive_dimension`        = `support_state` (always)
* `first_changed_dimension`   = `support_state` (always)
* `confidence_hold_noop`      = `True` (always)
* `identical_to_plateau_cause`= `False` (always)

DESi's machine-readable reason on all 14 cases:
`AUDIT_WITHDRAW_ON_FOREIGN_CAUSE`.

In plain language: the v3.35 Strategy B intervention's
`confidence_hold` component does no work in this corpus
(the confidence trace is flat at 0.25 from index n-3
onward for every plateau and every rescue), so the
rescue effect comes entirely from the audit-step
withdrawal. The withdrawal acts on `support_state`
regardless of the trajectory's cause class. The 14
rescued trajectories are all `CAUSAL_LEAP` (the plateau
cause is `CONFIDENCE_OSCILLATION`).

### 2. The two cohorts are geometrically separable (v3.38)

On the 34-trajectory mover universe:

* `separability`             = 1.00  (every trajectory's
  nearest neighbour is same-class)
* `overlap_rate`             = 0.00  (no cross-class pair
  is bit-identical)
* `manifold_count`           = 2     (disjoint)
* `cluster_purity`           = 1.00
* `pre_audit_perfect_separator_count` = 3

The three perfect pre-audit separators are
`frame_id@2`, `novelty@2`, and `frame_id@3`. The plateau
cohort carries `frame_id = 5.0` from state index 2
onwards; every rescued trajectory carries
`frame_id = 0.0` throughout. The verdict feature
(`support_state` at the final state) is also a perfect
separator but is, by definition, only knowable post-audit.

### 3. A pre-audit gate makes the rescue specific on the v3.35 universe (v3.39)

Four named selector policies plus the unselected baseline
were ablated:

| Selector | resolved | accidental | overcontrol | specificity | recall |
|---|---|---|---|---|---|
| `none` (baseline)             | 20 | 14 | 0 | 0.588 | 1.00 |
| `support_condition`           | 20 | 14 | 0 | 0.588 | 1.00 |
| `branch_cost_condition`       | 20 | 14 | 0 | 0.588 | 1.00 |
| `frame_stability_condition`   | 20 |  0 | 0 | **1.00** | 1.00 |
| `dual_trigger_condition`      | 20 |  0 | 0 | **1.00** | 1.00 |

The `frame_stability_condition` (and the equivalent
`dual_trigger_condition`) achieves both the v3.39 gates:
`specificity_score = 1.00 >= 0.90` and
`plateau_recall = 1.00 >= 0.90`. Strategy B is
plateau-specific on the v3.35 cross-class universe when
gated by `frame_id == 5.0` at index n-2.

### 4. Replay stability holds (v3.39)

`replay_stability = 1.00` across two full runs of all
five selectors.

## Why this is not unconditional GO

The named gates were defined on the v3.35 cross-class
universe (`plateau + causal_leap + support_decay +
frame_collision`, 36 trajectories). On the broader
corpus (395 trajectories), the same `frame_stability_condition`
selector fires on every non-plateau trajectory that
shares `frame_id = 5.0` at index n-2 — which includes
**145 SUPPORTED non-plateau trajectories**. The audit-
step withdrawal moves all 145 of them from
`support_state = 4.0` to `support_state = 0.0` (UNDER_AUDIT).

`full_corpus_overcontrol = 145` (rationale field in
`artifacts/v3_39/report.json`).

The v3.39 report's recommendation is therefore
`SPECIFICITY_LOCALLY_RECOVERED`, not
`SPECIFICITY_RECOVERED`. The Paper 10 text must include
this caveat verbatim: the pre-audit selector cannot
distinguish a plateau trajectory from a SUPPORTED
trajectory because both share an identical pre-audit
state at index n-2 (`frame_id=5.0`, `support_state=0.0`,
`confidence=0.25`, `branch_cost in {2.0, 3.0}`). The
distinction emerges only at the audit step itself
(plateau: support → 2.0; SUPPORTED: support → 4.0).

## What the paper must NOT claim

* That `frame_stability_condition` is a deployable rescue
  policy. It is plateau-specific only on the v3.35
  cliff-class universe. Deployed on the corpus it would
  overcontrol 145 healthy SUPPORTED trajectories.
* That DESi's interventions in general are specific. The
  v3.37 audit shows that Strategy B's `confidence_hold`
  component is a no-op in this corpus, leaving pure
  audit-withdrawal which is dimension-agnostic.
* That the plateau is a single subtype distinguished from
  CAUSAL_LEAP by any internal mechanism. The distinguishing
  feature is corpus-of-origin: v23 plateau trajectories
  enter frame 5; v314/v315 CAUSAL_LEAP trajectories never
  activate any frame. This is a dataset structure, not an
  epistemic structure.
* That re-auditing with confidence_hold would change any
  verdict. It would not — the `confidence_hold` floor
  equals the current confidence value at every index.

## Stop rules not triggered

* v3.37 `unexplained_cases` (0) is below the 0 ceiling.
* v3.38 `separability` (1.00) exceeds the 0.70 floor.
* v3.39 `specificity_score` (1.00) exceeds the 0.90 floor.
* v3.39 `plateau_recall` (1.00) exceeds the 0.90 floor.
* v3.39 `replay_stability` (1.00) meets the 1.0 anchor.

## Next sprint suggestion (out of scope for this document)

A v3.40 sprint that introduces a post-audit selector
(gate on `final support_state == 2.0`) would close the
full-corpus overcontrol gap by construction. This is a
trivial-but-honest fix: the rescue mechanism cannot be
pre-audit-specific in this corpus because the pre-audit
state vectors of plateau and SUPPORTED are
indistinguishable.
