# Cycle 6 proposal — validate_step_metric_coherence

Self-diagnosis (paper0/self_reflection.md §6.5, RPP-STR P03): no rule
flags steps with mutually-impossible metrics. Garbage in → confident
analysis out.

## Change

Add `validate_step_metric_coherence` to `diagnostics.py`. Flags steps
matching either impossibility:

- `dup_rate > 0.70 AND novel_claims >= 5`
- `dup_rate < 0.05 AND novel_claims == 0` (after loop 0)

Returns `StepCoherenceReport`. Added to `DeterministicMetrics`.

## Target failure

RPP-STR P03. Defensive coverage — no incoherent trajectory exists in
the n=10 set today.

## Expected metric improvement

- All 10 adversarial trajectories: `detected=False` (clean baseline).
- Tests 20 → 22.
- Forward-looking: activates on first real DES dump containing an
  incoherent metric row.

## Risk

Very low. No prompt change.

## Files

- `src/desi/diagnostics.py`
- `tests/test_diagnostics.py`
- `experiments/self_improvement/cycle_6/*.md`
- `README.md`

## Not in this cycle

No prompt change. Not yet wired into the LLM-side prefixes.
