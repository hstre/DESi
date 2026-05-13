# Cycle 3 — Window `detect_branch_explosion` averaging to the tail

## DESi self-diagnosis

n=20 cycle-2 metrics: `branch_explosion` fires on gen04 and gen17.
Both recover via late synthesis; the detector averages dup over the
whole trajectory, so early branch-explosion loops drag the average
down past 0.20 even after recovery.

Meanwhile gen06 and gen18 (`stagnation_then_branch`) do NOT fire even
though their LATE half is pure branch explosion — early stagnation
dilutes the whole-trajectory average out of the band.

The whole-trajectory averaging conflates "is this currently branching"
with "did this ever branch".

## Change

`detect_branch_explosion` now averages `dup_rate` and `novel_claims`
over the TAIL-3 instead of the full trajectory. `distinct_open_branches`
remains a full-history count.

## Predicted impact

- gen04: True → False (recovery suppresses) — _meta says correct.
- gen17: True → False (recovery suppresses) — _meta says correct.
- gen06: False → True (late branching now visible) — _meta says correct.
- gen18: False → True (late branching now visible) — _meta says correct.
- adv07: unchanged True (true positive maintained).
