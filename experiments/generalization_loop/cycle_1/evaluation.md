# Cycle 1 evaluation — tail-saturation guard on attractor detector

pytest **30 passed** (28 prior + 2 new for the guard).

## Metrics

| Metric | Baseline | Cycle 1 | Δ |
|---|---:|---:|---:|
| **n=20 attractor_lock fires** | 20 | **5** | -15 |
| **n=10 attractor_lock fires** | 9 | **5** | -4 |
| n=20 phase overlaps | 5 | 5 | 0 |
| n=10 phase overlaps | 3 | 3 | 0 |
| n=20 spurious-hit total | 30 | 15 | -15 |
| n=10 spurious-hit total | 17 | 13 | -4 |
| n=20 missed-hit total | 28 | 28 | 0 |
| malformed phase spans | 0 | 0 | 0 |
| pytest | 28 | **30** | +2 |

## Which fixtures still fire attractor_lock?

n=20 (5): `gen03_lock_recovery_lock`, `gen04_branch_explosion_with_recovery`,
`gen07_sparse_late_EN`, `gen15_high_EN_no_recovery_chain`,
`gen20_metric_incoherence_edge`. All five have tail mean_novel ≤ 3 AND
tail mean_dup ≥ 0.30 — genuine saturation, not focus-continuity noise.

n=10 (5): `adv01`, `adv03`, `adv04`, `adv06`, `adv08`. All five are
trajectories that decisively converged in the original suite design.

## Verdict

**ACCEPTED.** Pure precision improvement on a detector that was firing
indiscriminately. Recall (genuine attractor cases) is preserved.

## Next-cycle hint (from DESi self-diagnosis)

Top remaining issues from baseline+cycle 1:
1. **Phase overlaps: 5/20 fixtures still overlap** — gen03, gen07, gen10,
   gen13, gen14. Phase II and Phase V spans intersect in 3 of these;
   Phase III and Phase IV intersect in gen13.
2. **Missed-hits unchanged at 28/20** — prose expectations still flag.
3. **gen15 `high_EN_no_recovery_chain` should NOT trigger Phase III**
   (composite labels are all `genuine_transformation_unconfirmed`).

Cycle 2 candidate: enforce phase-span non-overlap (clip Phase II at
Phase V start; clip Phase III at Phase IV start). One detector change.
