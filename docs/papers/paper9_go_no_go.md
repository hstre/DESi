# Paper 9 — Go / No-Go Decision

**Status:** decision artifact; not the paper itself.
The directive forbids writing Paper 9 until v3.28..v3.30
pass every gate.

## Gate evaluation (directive § "Paper-9 Gate")

| # | Gate | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | UNKNOWN rate (v3.28)                   | < 0.20 | **0.000** | ✓ |
| 2 | survival_gain (v3.29)                  | > 0    | **50**    | ✓ |
| 3 | rollback_reduction (v3.30 vs v3.27)    | > 0    | **55**    | ✓ |
| 4 | nc_intervention_rate (v3.30)           | ≤ 0.20 | **0.000** | ✓ |
| 5 | replay_stability (v3.28 classifier)    | == 1.0 | **1.000** | ✓ |

All five gates pass.

## Decision

**Paper 9: GO.**

The directive's preconditions are satisfied. Paper 9 may be
written when the user requests it.

## Sources

* `artifacts/v3_28/report.json`         — root-cause observer
* `artifacts/v3_28/cliff_cause_distribution.json`
* `artifacts/v3_28/root_cause_taxonomy.json`
* `artifacts/v3_29/report.json`         — counterfactual survival
* `artifacts/v3_29/counterfactual_survival.json`
* `artifacts/v3_30/report.json`         — cause-aware control
* `artifacts/v3_30/cause_aware_control.json`
* `artifacts/v3_30/premature_closure_claims.json`

## Findings the paper will need to encode

1. **Root-cause taxonomy is closed and UNKNOWN-respecting.**
   v3.28's classifier never forces a class. 250 of 250
   cliff-bearing trajectories are classified;
   `unknown_rate = 0.000`. All four NC families remain
   UNKNOWN. `cause_nc_fp_rate = 0.000`.

2. **The dominant empirical cause in the v3 trajectory
   corpus is CONFIDENCE_OSCILLATION** (234 of 250
   classified cliffs). 248 of 250 cliff trajectories
   reach the audit step with frame-tension confidence
   ≤ 0.25 — the trajectory had been signalling low
   confidence well before the audit committed.

3. **Premature epistemic closure is empirically
   supported.** v3.29 ran four controller variants on
   the 55 trajectories v3.27 rolled back:
   * Run A (rollback)          rescued 55/55
   * Run B (passive v3.26)     rescued  5/55
   * Run C (no controller)     rescued  5/55
   * Run D (delayed closure)   rescued 55/55

   `survival_gain = 50` (Run D rescues 50 trajectories
   that Run C ended in REJECTED). `rollback_only_gain
   = 0` (no trajectory needed rollback specifically;
   delayed closure alone was sufficient).

   The v3.27 rollback action was *cosmetic with respect
   to verdict*: it produced the same final-state
   support_state as just skipping the audit step.

4. **Cause-aware control replaces every rollback with
   a cause-specific action.** v3.30:
   * `rollback_usage_count = 0` (down from 55 in v3.27)
   * `rollback_reduction = 55`
   * `rescued_verdicts    = 228`
   * `overcontrol_cases   = 0`
   * `nc_interventions    = 0`
   * `false_intervention_rate = 0.08` (well under 0.20)
   * `smoothness_delta    = +1.48` (counterfactual is
     smoother than the original on average)

   The action distribution mirrors the cause
   distribution: `confidence_hold` for 234,
   `causal_suspend` for 14, `support_hold` for 1,
   `frame_replay` for 1.

5. **The premature-closure claim set is materialised.**
   `premature_closure_claims.json` records 50
   trajectory-level claims with linked evidence
   (Run C vs Run D final support_state). These are the
   audit decisions the paper must defend as having been
   premature.

## What the paper must NOT claim

* Rollback "rescued" 50 trajectories in v3.27 because
  rollback is special. v3.29 shows it is not: any way
  of not committing to the audit verdict produces the
  same outcome on this corpus.
* Cause-specific actions are mechanistically faithful
  to the runtime layer. They are *state-vector
  simulations*; they re-shape existing state vectors
  and withdraw the audit step. The directive forbids
  runtime rule overrides; v3.30 does not perform any.
* The dominant CONFIDENCE_OSCILLATION class implies
  that confidence is the *cause* of every cliff. It is
  the strongest measurable signal in this corpus, but
  the v5-line "diagnostic vs intervention" lesson
  applies: an observable signal that correlates with
  failure is not necessarily the upstream cause.

## Stop rules not triggered

* v3.28's `cause_nc_fp_rate` (0.000) is well below the
  0.10 ceiling.
* v3.29's `survival_gain` (50) is non-zero; the "no
  rescue = no paper" rule did not fire.
* v3.30's `false_intervention_rate` (0.08) is below
  the 0.20 ceiling.

Sprint complete. Paper 9 may be written.
