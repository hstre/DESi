# Cycle 4 — Tighten ATTRACTOR_TAIL_MIN_MEAN_DUP comparison (>= to >)

## Self-diagnosis

gen04 still fires `attractor_lock` after cycle 1. Its tail (loops 5-7) has
mean_novel = 3.0 (right at `<= 3.0`) and mean_dup = 0.30 (right at `>=
0.30`). The cycle-1 thresholds were INTENTIONALLY LOOSE. gen04
demonstrates the boundary case is a false positive (the trajectory
recovered via synthesis).

## Change

Swap `mean_dup >= ATTRACTOR_TAIL_MIN_MEAN_DUP` to
`mean_dup > ATTRACTOR_TAIL_MIN_MEAN_DUP`.

## Predicted impact

- n=20 attractor_lock fires: 5 → 4 (gen04 released).
- n=10 attractor_lock fires: 5 → 5.
- No DET-FAL counter movement.
