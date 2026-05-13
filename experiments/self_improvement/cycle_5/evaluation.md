# Cycle 5 evaluation — detect_mild_stagnation

## Tests

pytest 18 → **20** passed (positive + negative regressions).

## Metrics (n=10 adversarial)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `false_positive_count` (DET-FAL) | 2 | 2 | 0 |
| `false_negative_count` (DET-FAL) | 3 | **2** | **−1** |
| Trajectories with `mild_stagnation.detected=True` | 0 | **1** (adv04) | +1 |
| Trajectories with `mild_stagnation` *and* Phase V firing concurrently | 0 | 0 | 0 |
| Runtime cost | 0 | 0 | 0 |

### Per-trajectory mild_stagnation

```
adv01: phase_v=True  -> suppressed
adv02: tail_mean_novel=2.8, not strictly increasing -> no
adv03: phase_v=True  -> suppressed
adv04: tail_mean_novel=2.0, dup strictly increasing -> DETECTED
adv05: tail_mean_novel=6.0 -> no
adv06: phase_v=True  -> suppressed
adv07: tail_mean_novel=8.0 -> no
adv08: phase_v=True  -> suppressed
adv09: phase_v=True  -> suppressed
adv10: phase_v=True  -> suppressed
```

## Regressions

None.

## Unexpected effects

adv01 has `tail_mean_novel=0.4` and `dup_strictly_inc=True` — would
fire on the soft criteria alone, but the Phase V guard correctly
suppresses (adv01 is already in Phase V loops 3..5). Confirms the
guard works.

## Verdict

**ACCEPTED.** false_negative_count 3 → 2; zero false positives;
zero overlap with Phase V.

## Next cycle hint

Cycle 6 candidate: `validate_step_metric_coherence` (§6.5 / RPP-STR
P03) — quarantine steps with mutually impossible metrics.
