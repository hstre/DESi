# Cycle 8 evaluation

pytest 25 → **26**.

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `false_positive_count` (DET-FAL) | 2 | **1** | **−1** |
| `false_negative_count` (DET-FAL) | 2 | 2 | 0 |
| adv06 `has_candidate` | True | **False** | resolved |

## Per-trajectory penultimate after cycle 8

```
adv01..adv02, adv04, adv07..adv10: has_candidate=False (correct)
adv03: has_candidate=True (correctly: penultimate loop 3 confirmed)
adv05: has_candidate=False (last EN is also confirmed)
adv06: has_candidate=False (was True under legacy classifier; T6 resolved)
```

## Verdict

**ACCEPTED.** DET-FAL false_positive_count 2 → 1. Only remaining FP
is T5 (Phase II false positive on adv05 oscillation).

## Next cycle hint

Cycle 9: Phase II persistence requirement (§4.3, RPP-STR adv05) —
require novel<=2 across ≥2 consecutive loops to fire Phase II.
