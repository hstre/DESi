# Cycle 3 evaluation — Phase II without EN

## Tests

pytest 15 → 16. New `test_phase_ii_fires_without_en_events` added
first, confirmed failing on pre-cycle code, passes after fix. All
prior tests still pass.

## Metrics (n=10 adversarial)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `malformed_phase_span_count` | 0 | 0 | 0 |
| `false_positive_count` (DET-FAL) | 2 | 2 | 0 |
| `false_negative_count` (DET-FAL) | 5 | **4** | **−1** |
| Phase II no-EN FN count | 2 | **0** | −2 |
| Runtime cost | 0 | 0 | 0 |

### Per-trajectory Phase II change

```
adv04: (no Phase II)  ->  II 2..2 confidence=low
adv08: (no Phase II)  ->  II 4..4 confidence=low
all others: unchanged
```

DET-FAL FN count drops by 1 (not 2) because the falsification ledger
originally counted Phase II FN as a single class
(phase_ii_no_en). adv08 fully resolved; adv04 gains Phase II but the
underlying stagnation signal (no hard threshold crossing) still
needs the mild-stagnation detector in a later cycle.

## Regressions

None.

## Unexpected effects

First use of `confidence="low"` in the phase-span output surface.
Downstream report-writer handles arbitrary confidence strings, so no
breakage.

## Verdict

**ACCEPTED.** false_negative_count 5→4; adv04+adv08 restored; zero
regressions.

## Next cycle

Cycle 4 candidate: detect_mild_stagnation (closes adv04's underlying
stagnation signal). Or detect_branch_explosion (T7).
