# Cycle 4 evaluation — detect_branch_explosion

## Tests

pytest 16 → **18** passed (positive + negative regressions added).
Negative regression confirms attractor-lock shape does NOT trigger
the detector. Positive regression confirms a 6-loop branch-fanout
shape DOES trigger.

## Metrics (n=10 adversarial)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `false_positive_count` (DET-FAL) | 2 | 2 | 0 |
| `false_negative_count` (DET-FAL) | 4 | **3** | **−1** |
| Trajectories emitting `branch_explosion.detected=True` | 0 | 1 (adv07) | +1 |
| Trajectories emitting `branch_explosion.detected=True` *incorrectly* | 0 | 0 | 0 |
| Runtime cost | 0 | 0 | 0 |

### Per-trajectory branch_explosion (post cycle 4)

```
adv07: detected=True  branches=10 dup=0.10 novel=8.5  <-- the only positive case
all others: detected=False (cleanly: distinct_open_branches=0 on 9/10 trajectories)
```

DET-FAL T7 (branch-explosion FN) is resolved.
`false_negative_count` 4 → 3.

## Regressions

None on the n=10 set.

## Unexpected effects

- `DeterministicMetrics` gained one field (`branch_explosion`).
  Downstream consumers that destructure `metrics` by position or
  use `asdict()` may produce a slightly different shape; the only
  current consumer (`report_writer.py`) accesses fields by name, so
  no breakage. Noted for `final_report.md`.

## Verdict

**ACCEPTED.** false_negative_count 4 → 3; zero new false positives;
adv07 pathology now visible.

## Next cycle hint

Cycle 5 candidate from self_reflection.md §6.2:
`detect_mild_stagnation` — closes the remaining adv04 stagnation
signal.
