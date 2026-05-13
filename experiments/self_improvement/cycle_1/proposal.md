# Cycle 1 proposal — fix malformed phase span invariant

**DESi self-diagnosis** (from `paper0/self_reflection.md §7.7`, the
lowest-cost item on the "what would most likely break DESi next" list):

> The span-invariant bug DET-FAL T10 Phase II `loops 3..2` is still
> present in `phase_detector.py`. Will silently leak into reports any
> time Phase II fires on a trajectory where the first novelty collapse
> precedes the first EN event.

## Proposed change

`src/desi/phase_detector.py::detect_phase_ii` constructs a `PhaseSpan`
with `start_loop=collapse_loop, end_loop=trigger_loop`. When the first
EN event fires at a loop *before* the first novelty-collapse loop, this
yields `start_loop > end_loop` (DET-FAL T10: novelty collapses at loop
3, first EN at loop 2 → reported as `loops 3..2`).

The fix is one line: when constructing the Phase II span, enforce
`start, end = min(collapse_loop, trigger_loop), max(collapse_loop,
trigger_loop)`. The semantic intent of Phase II — "the window between
novelty collapse and first EN" — is preserved either way; the
orientation of that window is arbitrary.

## Target failure

DET-FAL T10 (random walk) — the single span-invariant bug recorded by
the prior falsification pass. The bug surfaces on any trajectory where
the first EN precedes the first novelty collapse, which is a real
ordering observed in production trajectories where EN probes are
front-loaded.

## Expected metric improvement

- `malformed_phase_span_count` across the 10 adversarial trajectories:
  expected baseline 1 (T10), expected post-fix 0.
- No expected change to any LLM-side metric (cycle is purely
  deterministic).
- All 13 existing pytest cases must still pass; one new test added
  for the T10-shape regression.

## Risk

- **Low.** The fix is a single-line normalisation; the only way it
  regresses is if some downstream consumer relies on the orientation
  `(collapse_loop, trigger_loop)` rather than `(min, max)`. No such
  consumer exists in the current code (the only readers are the
  report writer, which renders `start..end`, and the test suite).
- The fix changes the *reported* phase II span on one out of 10
  adversarial trajectories. Downstream LLM role outputs for T10 would
  cite the corrected span — but we will not re-run the LLM evaluation
  in this cycle, since the prefix policy didn't change and the
  rule-policy decision rule (paper0) does not depend on phase II's
  exact boundary order.

## Files expected to change

- `src/desi/phase_detector.py` — one-line edit inside `detect_phase_ii`.
- `tests/test_phase_detector.py` — one new regression test
  (`test_phase_ii_span_is_well_ordered`) that constructs a T10-shape
  trajectory and asserts `start_loop <= end_loop`.
- `experiments/self_improvement/cycle_1/{proposal.md, evaluation.md}`.
- `README.md` — append the cycle-1 row to the "Self-improvement loop
  log" table (added by this cycle).

## What this cycle does NOT change

- No prompt changes.
- No new metrics; `malformed_phase_span_count` is computed
  ad-hoc by counting `span.start_loop > span.end_loop` across the
  outputs of `detect_phases()`. It is not added to the production
  scorer in `paper0/run_role_policy_experiment.py`.
- No new detectors.
- No DES-side model or operator changes.
