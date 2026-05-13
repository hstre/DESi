# Cycle 9 — Phase II persistence requirement

Self-diagnosis: cycle-8 hint + paper0/self_reflection.md §4.3 (T5
adv05 oscillation false positive).

## Change

`detect_phase_ii` requires `novel_claims<=2` on TWO consecutive
loops. Pre-cycle-9 a single-loop dip fired Phase II.

## Target

DET-FAL T5 (adv05). Also dampens adv10 random walk.

## Expected metric

- adv05 Phase II: fires → does NOT fire.
- adv10 Phase II: fires → does NOT fire.
- DET-FAL `false_positive_count` 1 → 0.
- 26 → 27 pytest cases.

## Risk

Updated `test_phase_ii_span_is_well_ordered` (trajectory extended to
loop 4 to satisfy persistence). New negative regression added.
