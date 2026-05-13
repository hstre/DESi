# Cycle 3 proposal — Phase II without EN (saturation-without-EN)

Self-diagnosis (paper0/self_reflection.md §4.3 + §6.3): Phase II
short-circuits on `not trajectory.en_events`. DET-FAL T8 (monotonic
decline with zero EN events) never enters Phase II.

## Change

Remove the EN-gate from `detect_phase_ii`. When no EN events exist,
emit Phase II at the collapse loop with confidence="low" and
evidence "no EN events in trajectory". When EN events exist,
behaviour is unchanged.

## Target failure

DET-FAL T8 — adv04 and adv08 (no-EN trajectories) currently emit no
Phase II.

## Expected metric improvement

- adv04 and adv08 now emit Phase II at low confidence.
- DET-FAL `false_negative_count` 5 → 4.
- One new pytest case.

## Risk

Low. Branch is `first_en is None` gated; pre-existing EN-bearing
branch unchanged. False-positive risk on trajectories with a brief
novel≤2 dip is mitigated by the "low" confidence label.

## Files

- src/desi/phase_detector.py (detect_phase_ii body)
- tests/test_phase_detector.py (new test_phase_ii_fires_without_en_events)
- experiments/self_improvement/cycle_3/*.md
- README.md (loop-log row)

## Not in this cycle

No prompt changes. No mild-stagnation detector. No metric coherence
rules. Those are separate cycle candidates.
