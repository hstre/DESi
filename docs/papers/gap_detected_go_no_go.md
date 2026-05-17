# GAP_DETECTED Residual — Concept Gate Decision

**Status:** concept-gate artifact for the GAP_DETECTED
Residual Audit Sprint (v3.46–v3.48). Per the
directive's wording ("Noch kein Paper") this document
records that the Concept Gate is met and that the
research direction may continue; it is not yet a Paper
10-style decision.

## Concept Gate evaluation (directive § "Concept Gate")

| # | Gate                          | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | terminal_gap_count (v3.46)    | >= 2      | **2**     | ✓ |
| 2 | replay_stability (all sprints)| == 1.00   | **1.00**  | ✓ |
| 3 | gap_cluster_count (v3.47)     | >= 1      | **1**     | ✓ |
| 4 | resolved_count OR robust terminal class (v3.48) | resolved > 0 OR class proven | **resolved = 2** | ✓ |

All four Concept Gate conditions are met.

## Decision

**Concept Gate: PASS.** The GAP_DETECTED residual is a
real, deterministic, geometrically-isolated cohort
with a recoverable verdict structure. The directive's
"Sind sie Restmüll oder neuer Mechanismus?" question
resolves to: **neuer Mechanismus** — distinct from
plateau in cohort geometry (orphan manifold), in cause
class (SUPPORT_DECAY vs the plateau's
CONFIDENCE_OSCILLATION), and in source corpus (sample
8-state vs v23/v314/v315 5-state).

This is not a paper. The next sprint may explore the
mechanism in depth; Paper 10 v4 remains the active
decision document for the plateau / leakage axis.

## Sources

* `artifacts/v3_46/report.json`               — GAP census
* `artifacts/v3_46/gap_inventory.json`        — 2 GapCase records
* `artifacts/v3_47/report.json`               — GAP geometry
* `artifacts/v3_47/gap_geometry.json`         — per-GAP nearest anchors
* `artifacts/v3_48/report.json`               — resolution strategies
* `artifacts/v3_48/gap_resolution.json`       — 14 per-strategy outcomes
* `artifacts/v3_48/terminal_gap_claims.json`  — 2 per-GAP claims

## Findings the concept memo must encode

### 1. The 2 cases are real and exactly match Paper 10 (v3.46)

* `gap_detected_count` = 2
* `terminal_gap_count` = 2 (matches Paper 10's
  documented 2 GAP non-rescued cases)
* `transient_gap_count` = 0
* `gap_outside_non_rescued` = 0
* `source_corpus_distribution` = `{"sample": 2}`
* `gap_replay_stability` = 1.00

The 2 cases are `sample:n03_darwin` (8-state, single
final-GAP) and `sample:n03_mozart` (8-state, MID_RUN
GAP at indices 6 and 7).

### 2. The GAP cohort is an orphan manifold (v3.47)

Tail-aligned 45-d trajectory vectors:

* `gap_to_plateau_distance_mean` ~ 12-15
  (jitters under hash-seed; orphan check is stable)
* `gap_to_leakage_distance_mean` ~ 13-16
  (consistently the farthest cohort)
* `gap_to_rescued_distance_mean` ~ 12-15
* `gap_is_orphan_manifold` = `true`
  (min observed distance over a 12-seed sweep is 11.25,
  well above the 5.0 floor; the plateau cohort's
  internal pairwise distances are 0.0..3.18 for
  context)
* `gap_cluster_count` = 1 (the two GAP cases form a
  single 1-NN component)
* `gap_cause_distribution` =
  `{"SUPPORT_DECAY": 2}` or
  `{"SUPPORT_DECAY": 1, "FRAME_COLLISION": 1}`
  (darwin's primary jitters between the two near-tied
  causes across hash seeds; mozart is stably
  SUPPORT_DECAY)
* `cause_identity_match_plateau` = `false` (neither
  case primary-classifies as CONFIDENCE_OSCILLATION,
  the plateau cause anchor)

### 3. Resolution strategies (v3.48)

Seven closed strategies applied to both GAP cases:

| Strategy                  | Resolved | Unresolved | Overcontrol | NC FP |
|---------------------------|----------|------------|-------------|-------|
| A_no_change               | 0        | 2          | 0           | 0.00  |
| B_confidence_hold         | 1        | 1          | 145         | 1.00  |
| C_audit_delay             | 2        | 0          | 145         | 1.00  |
| **D_bridge_expansion**    | **2**    | **0**      | **0**       | **0.00** |
| E_premise_re_extraction   | 0        | 2          | 0           | 0.00  |
| F_frame_replay            | 1        | 1          | 145         | 1.00  |
| **G_bridge_and_premise**  | **2**    | **0**      | **0**       | **0.00** |

* `best_strategy` = `D_bridge_expansion`
* `resolved_count` = 2  (Concept Gate #4 PASS)
* `unresolved_count` = 0
* `overcontrol` = 0
* `nc_resolution_fp` = 0.00
* `terminal_failure_class` = `false`
* `replay_stability` = 1.00
* Recommendation: `GAP_FULLY_RESOLVED`

Two clean strategies (D and G, both gated on
final == GAP_DETECTED) resolve both GAP cases without
overcontrolling any healthy SUPPORTED trajectory.
The v3.33-style Strategy B (confidence_hold + audit-
withdraw) resolves only darwin (mozart's pre-audit
anchor is also GAP, so the withdrawal yields GAP
again) and overcontrols 145 leakage trajectories on
the broader corpus. The audit_delay strategy (C)
re-anchors on states[-3] and resolves both but with
the same 145 overcontrol.

DESi's internal answer to the directive's question
"Sind die 2 GAP_DETECTED-Fälle bloßer Restmüll oder
ein neuer Mechanismus?": **neuer Mechanismus.** The
GAP cohort has its own primary cause
(SUPPORT_DECAY), its own corpus origin (sample
8-state), its own geometric region (orphan manifold,
distance >= 11 from every other cohort), and admits
its own non-destructive resolution policy
(bridge expansion). It does NOT respond to the
plateau-tuned Strategy B in the same way the plateau
does.

## What the memo must NOT claim

* That `D_bridge_expansion` is a deployable rescue
  policy. It is gated on the post-audit verdict
  (final == GAP_DETECTED) — a re-intervention, not a
  forecasting predicate. Same limitation as the v4
  Paper 10 v3 caveat on the radius-bounded selector.
* That all GAP_DETECTED trajectories anywhere will
  carry SUPPORT_DECAY as their primary cause. The
  v3.32 classifier's near-tie between SUPPORT_DECAY
  and FRAME_COLLISION on darwin is corpus-specific
  and hash-seed dependent.
* That `bridge_expansion` is "correct" in any
  audit-semantic sense. It promotes a GAP verdict
  to BRIDGE_REQUIRED — a less-committed verdict, not
  a SUPPORTED verdict. The audit's GAP outcome was
  protocol-correct; bridge_expansion only relaxes
  the verdict to "still needs bridging" rather than
  "explicit gap".
* That the 2-case cohort generalises to larger
  GAP populations on other corpora. The v5-line
  probe lesson applies: this is one corpus's
  empirical GAP residual.

## Stop rules not triggered

* v3.46 `terminal_gap_count` (2) meets the Paper-10
  anchor.
* v3.46 `gap_replay_stability` (1.00) meets the 1.0
  anchor.
* v3.47 `gap_cluster_count` (1) meets the Concept
  Gate #3 floor.
* v3.47 `replay_stability` (1.00) meets the 1.0
  anchor.
* v3.48 `resolved_count` (2) is strictly positive;
  GAP is not a robust terminal failure class.
* v3.48 `replay_stability` (1.00) meets the 1.0
  anchor.

## Next direction (out of scope for this document)

A future sprint may investigate:

1. Whether `D_bridge_expansion` corresponds to any
   audit-semantic operation other than verdict
   relaxation — i.e. whether escalating GAP to
   BRIDGE_REQUIRED carries epistemic content beyond
   "we did not commit".
2. Whether the SUPPORT_DECAY / FRAME_COLLISION
   tie on darwin reflects a measurement issue
   (frame_detector hash-seed jitter) or a genuine
   joint causation. v3.49 could anchor the
   classifier on a stable canonical ordering.
3. Whether longer trajectories (n > 5) systematically
   produce GAP residuals in other corpora, or whether
   the sample corpus's 8-state shape is the necessary
   condition.
