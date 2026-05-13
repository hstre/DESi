# Cycle 9 evaluation — Phase II persistence

## Tests

pytest 26 → **27**. Existing span-ordering test trajectory extended
to loop 4. New `test_phase_ii_does_not_fire_on_single_loop_dip`.

## Metrics (n=10 adversarial)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `false_positive_count` (DET-FAL) | 1 | **0** | **−1** |
| `false_negative_count` (DET-FAL) | 2 | 2 | 0 |
| adv05 Phase II | fires | **does not** | T5 resolved |
| adv10 Phase II | fires | does not | single-dip silenced |

## Per-trajectory Phase II (post cycle 9)

```
adv01: 1..1   adv06: 1..3
adv02: 1..2   adv07: (no)
adv03: 1..2   adv08: 4..4
adv04: 2..2   adv09: 2..2
adv05: (no)   adv10: (no)
```

## Verdict

**ACCEPTED.** DET-FAL FP → 0. Remaining 2 FNs (T1, T2) require Phase
III to consume the composite EN classifier (cycle 10 candidate).

## Next cycle hint

Cycle 10: Phase III ∩ Phase V mutual exclusion + Phase III on
composite EN classifier. The combined fix resolves T1+T2.
