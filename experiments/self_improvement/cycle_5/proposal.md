# Cycle 5 proposal — detect_mild_stagnation

Self-diagnosis (paper0/self_reflection.md §4.2 + §6.2): DET-FAL T4
(adv04 — novel sits at ~2, dup creeps 0.35→0.45 but never crosses
0.50) is invisible. Phase V's hard cut-off (`dup>0.50 ∧ novel≤1`)
never trips; adv04 produced only Phase I.

## Change

Add `detect_mild_stagnation` to `diagnostics.py`. Soft trigger:

    tail of last 5 steps
    AND mean(novel_claims) ≤ 2.5
    AND dup strictly increasing across tail
    AND no genuine EN event in tail
    AND no Phase V hard trigger anywhere in the trajectory

The last clause is the *coexistence guard*: mild stagnation is for
trajectories Phase V misses, not for trajectories Phase V already
covers.

## Target failure

DET-FAL T4 — adv04.

## Expected metric improvement

- adv04 emits `mild_stagnation.detected=True`.
- 9 other trajectories: `detected=False`.
- DET-FAL `false_negative_count` 3 → 2.
- 18 → 20 pytest cases.

## Risk

Low. Phase V guard prevents the most common overlap. False-positive
risk lives in trajectories where novel briefly drops below 2.5 with
dup creeping; the 3-loop minimum window mitigates this.

## Files

- `src/desi/diagnostics.py`
- `tests/test_diagnostics.py`
- `experiments/self_improvement/cycle_5/*.md`
- `README.md`

## Not in this cycle

No prompt changes. No phase model change. Metric coherence and
composite EN are separate cycle candidates.
