# Cycle 4 proposal — detect_branch_explosion

Self-diagnosis (paper0/self_reflection.md §6.1, top of new-detector
queue): branch-explosion pathology (DET-FAL T7) was invisible. DESi
emitted only Phase I + a medium-confidence Phase V from
`terminal_failure_mode=GRAPH_TOO_LARGE`. The pathology itself —
sustained open branches + low dup + high novel — had no rule.

## Change

Add `detect_branch_explosion` to `diagnostics.py`. Returns a
`BranchExplosionReport` with `detected: bool` plus the three
component signals (distinct open branches, avg dup_rate, avg novel).
Trigger:

    distinct branch_open=True claim ids >= 5
    AND avg dup_rate < 0.20
    AND avg novel_claims >= 5

Add to `DeterministicMetrics`, surfaced through `compute_all`.

## Target failure

DET-FAL T7 — adv07. Currently the only signal is
`terminal_failure_mode=GRAPH_TOO_LARGE`; the explosion shape itself
has no detector.

## Expected metric improvement

- adv07 emits `branch_explosion.detected=True`; all other 9
  trajectories emit `detected=False`.
- No false positive on the n=10 set.
- 17 → 18 pytest cases.
- Goal: convert one DET-FAL false negative (the silent
  branch-pathology case) into a detected signal.

## Risk

Low on the adversarial set (only adv07 has any branch_open
claims). On real DES paper7/paper8 trajectories that use normal
multi-branch exploration, the k=5 threshold may fire. Calibration
hooks (the three constants
`BRANCH_EXPLOSION_MIN_BRANCHES`, `BRANCH_EXPLOSION_MAX_AVG_DUP`,
`BRANCH_EXPLOSION_MIN_AVG_NOVEL`) sit at module scope so they can
be tuned without changing call sites.

## Files

- `src/desi/diagnostics.py` (new function + dataclass + compute_all wiring)
- `tests/test_diagnostics.py` (positive + negative regression tests)
- `experiments/self_improvement/cycle_4/*.md`
- `README.md` (loop-log row)

## Not in this cycle

No prompt changes. No new phase. Report-writer surfacing of the new
field is left for a future cycle (the metric is reachable on
`metrics.branch_explosion` for any consumer).
