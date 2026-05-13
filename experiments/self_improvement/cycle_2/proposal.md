# Cycle 2 proposal — close Phase V on reversal

**DESi self-diagnosis** (from cycle-1 next-cycle hint + 
`paper0/self_reflection.md §4.4 + §6.4`): the Phase V detector is
sticky. Once it fires at loop *i*, it sets `end_loop` to the last loop
of the trajectory unconditionally, even if the trigger condition stops
holding for the rest of the run. DET-FAL T9 is the canonical
example: Phase V fires at loop 2, the trajectory recovers from loop 6
onward, but the reported Phase V span is `loops 2..8` — covering the
recovery.

## Proposed change

`src/desi/phase_detector.py::detect_phase_v` — when Phase V's hard
trigger fires at loop `start`, walk the post-trigger steps and close
the span at the **last loop where the trigger condition still held**
once it has stopped holding for ≥2 consecutive subsequent loops. Add a
trigger-evidence line noting the closure.

Algorithm:

    last_held = start
    consecutive_broken = 0
    for s in sorted_steps after start:
        if dup > 0.50 AND novel <= 1:
            last_held = s.loop_index
            consecutive_broken = 0
        else:
            consecutive_broken += 1
            if consecutive_broken >= 2:
                break   # phase-V trigger has been broken
    end_loop = last_held if closed else sorted_steps[-1].loop_index

This implements the §6.4 "phase-reversal detector" recommendation by
closing the span at the last loop where the trigger held. Phase III's
mutual exclusion (§6.4 second clause) is **NOT** done in this cycle —
that is a separate concern; one change per cycle.

## Target failure

DET-FAL T9 — Phase V is sticky; reports `loops 2..8` instead of
closing at the reversal. The current behaviour overstates terminal
convergence on any trajectory that recovers after crossing the
threshold.

## Expected metric improvement

- adv09 Phase V span: `loops 2..8` (sticky) → `loops 2..5` (closed at
  last loop where condition held; loops 6..8 fall outside the span).
- `false_positive_count` (DET-FAL): one of the four FPs was T9's
  "Phase V claims the recovery region". Expected: 4 → 3.
- All 14 existing pytest cases still pass; one new regression test
  for the T9-shape reversal.
- No LLM rerun (no prompt change).

## Risk

- **Low-medium.** Two existing tests verify Phase V triggers; they
  both use trajectories that end inside the Phase V window
  (`test_phase_v_triggers_on_dup_high_and_novel_low`,
  `test_terminal_failure_alone_triggers_phase_v_with_medium_confidence`),
  so the closure logic won't be exercised — they should still pass.
- Risk vector: a trajectory where Phase V's condition briefly fails
  (one loop) and then resumes. The k=2-consecutive rule absorbs this;
  a single false-positive recovery loop will not close Phase V.
- The terminal-failure-mode-only fallback branch (`detect_phase_v`
  emits Phase V at the last loop when no step crosses the hard
  threshold but `terminal_failure_mode` is set) is **untouched** by
  this cycle — that branch already produces a single-loop span and
  has no reversal concern.

## Files expected to change

- `src/desi/phase_detector.py` — body of `detect_phase_v`'s
  trigger-step branch.
- `tests/test_phase_detector.py` — one new regression test
  (`test_phase_v_closes_on_reversal`).
- `experiments/self_improvement/cycle_2/{proposal.md, evaluation.md}`.
- `README.md` — append cycle-2 row to the loop-log table.

## What this cycle does NOT change

- No prompt changes.
- No Phase III ∧ Phase V mutual exclusion (separate cycle candidate).
- No change to the terminal-failure-only branch of `detect_phase_v`.
- No new metric in the production scorer.
- No DES-side model or operator changes.
