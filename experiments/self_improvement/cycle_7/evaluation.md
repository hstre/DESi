# Cycle 7 evaluation — composite EN classification

## Tests

pytest 22 → **25**.

## Metrics (n=10 adversarial)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `false_positive_count` (DET-FAL) | 2 | 2 | 0 (legacy unchanged) |
| `false_negative_count` (DET-FAL) | 2 | 2 | 0 (legacy unchanged) |
| EN events where composite-label disagrees with legacy | n/a | **3** | new signal |
| Runtime cost | 0 | 0 | 0 |

Composite labels surface key distinctions on:

```
adv01 loop 1: legacy=genuine_transformation -> composite=genuine_transformation_unconfirmed
adv02 loop 2: legacy=borderline             -> composite=borderline_with_recovery
adv06 loop 3: legacy=genuine_transformation -> composite=genuine_transformation_unconfirmed
adv10 loop 4: legacy=local_variation_or_false_return -> composite=low_eni_with_unexpected_recovery
```

## Verdict

**ACCEPTED** (capability). The classification *capability* is added
this cycle; the counters don't move because existing consumers
(penultimate, Phase III) still use the legacy classifier. Cycle 8
switches the penultimate principle to composite.

## Next cycle hint

Cycle 8: switch `detect_penultimate_en_candidate` to use
`classify_en_event_composite`. Resolves DET-FAL T6 (adv06
false-positive penultimate candidate).
