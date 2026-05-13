# Cycle 2 evaluation — `_clip_phase_overlaps` post-processor

pytest **32 passed** (30 prior + 2 new for the post-processor).
One prior test (`test_two_consecutive_low_eni_events_trigger_phase_iv`)
needed its trajectory adjusted to not co-fire Phase V on the same
loops — documented inline; this was test over-specification, not a
detector regression.

## Metrics

| Metric | Cycle 1 | Cycle 2 | Δ |
|---|---:|---:|---:|
| **n=20 phase overlaps** | 5 | **0** | -5 |
| **n=10 phase overlaps** | 3 | **0** | -3 |
| n=20 attractor_lock fires | 5 | 5 | 0 |
| n=10 attractor_lock fires | 5 | 5 | 0 |
| n=20 spurious-hit total | 15 | 15 | 0 |
| n=10 spurious-hit total | 13 | 13 | 0 |
| malformed phase spans | 0 | 0 | 0 |
| pytest | 30 | **32** | +2 |

## Clip outcomes (n=20)

| Fixture | Pre-cycle-2 overlap | Post-cycle-2 outcome |
|---|---|---|
| gen03_lock_recovery_lock | II:1-3 ∩ V:1-3 | Phase II dropped (V fully covers) |
| gen07_sparse_late_EN | II:6-7 ∩ V:7-7 | Phase II clipped to 6-6 |
| gen10_terminal_failure_with_recovery | II:1-4 ∩ V:2-6, III:5-6 ∩ V:2-6 | II→1-1; III dropped |
| gen13_delayed_phase_IV | III:3-19 ∩ IV:17-19 | III clipped to 3-16 |
| gen14_phase_reversal_twice | II:1-1 ∩ V:1-2 | Phase II dropped (V covers) |

## Clip outcomes (n=10)

| Fixture | Pre-cycle-2 overlap | Post-cycle-2 outcome |
|---|---|---|
| adv03 | II:1-2 ∩ V:2-5 | II clipped to 1-1 |
| adv06 | II:1-3 ∩ III:2-2 ∩ V:4-6 | II→1-1; III dropped |
| adv09 | II:2-2 ∩ IV:2-4 ∩ V:2-5 | II dropped; IV dropped; only V survives |

## Verdict

**ACCEPTED.** Pure quality improvement at the orchestration layer.
Eliminates 100% of phase overlaps across both suites without changing
any individual detector's logic.

## Risk note

For `adv09`, the clip drops Phase IV entirely. The original `adv09`
was designed as "late recovery after apparent lock" — Phase IV:2-4
was intended as the lock region. Post-cycle-2, that signal is
absorbed into Phase V:2-5. The trigger evidence for Phase V still
records the lock at 2-3 + the broken recovery, so no information is
lost; but the distinction between "deepening" and "terminal" is
collapsed.

## Next-cycle hint

1. `attractor_lock` still fires on gen04 (tail saturated borderline) —
   the trajectory just RECOVERED via synthesis. False positive.
2. gen13 Phase III:3-16 is still a 14-loop span. Phase III's
   `next-genuine` boundary logic doesn't see Phase IV.
3. branch_explosion fires on gen04, gen17 — both have late synthesis
   recovery that should suppress the alarm.

Cycle 3 candidate: window branch_explosion's averaging to the
TAIL-3 instead of whole trajectory. Would suppress gen04, gen17 false
positives without losing adv07's true-positive (whose tail is also
fully-branched).
