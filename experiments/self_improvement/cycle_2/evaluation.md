# Cycle 2 evaluation — close Phase V on reversal

## Tests

| Suite | Before | After |
|---|---|---|
| pytest (all) | 14 passed | **15 passed** (one regression test added) |
| New test `test_phase_v_closes_on_reversal` | failed (asserts `4 == 7`) | passes |

The regression test was added first and confirmed to fail on the
pre-cycle codebase. The detector change was then applied. The test
passes; all 14 prior tests still pass.

## Implementation detail (post-smoke refinement)

The first implementation closed Phase V at the last loop where the
trigger held, *regardless* of `terminal_failure_mode`. This regressed
adv03: `V loops 2..5` → `V loops 2..2`, because adv03 has an EN-driven
dip at loops 3-4 before locking at loop 5 with `terminal_failure_mode
= ATTRACTOR_LOCK`. The dip was misread as a reversal.

The accepted implementation gates the closure on `terminal_failure_mode`:

- If `has_terminal_failure` is true (the trajectory authoritatively
  locked), Phase V extends to end-of-trajectory regardless of
  transient recoveries.
- If `has_terminal_failure` is false (no recorded terminal lock),
  walk forward and close the span at the last loop where the trigger
  held, once it has stopped holding for ≥2 consecutive subsequent
  loops.

This preserves adv03 while still fixing T9. The refinement is
recorded here so the failed-then-revised attempt isn't lost.

## Primary-metrics table (before/after)

Measured on `data/adversarial/*.json`. Other metrics are LLM-side and
unchanged this cycle (no prompt change).

| Metric                              | Before | After | Delta |
|-------------------------------------|-------:|------:|------:|
| `malformed_phase_span_count`        |      0 |     0 |     0 |
| `false_positive_count` (DET-FAL)    |      4 |  **3** |   −1 |
| `false_negative_count` (DET-FAL)    |      5 |     5 |     0 |
| Phase V span covering adv09 recovery (loops 6..8) | yes (sticky) | **no** | resolved |
| `phase_overlap_count` (RPP-EMP B mean) |  0.20 |   n/a | no LLM rerun |
| `unsupported_claims` (RPP-EMP B mean)  |  2.80 |   n/a | no LLM rerun |
| `hallucinated_causal_claims` (RPP-EMP B mean) | 2.30 | n/a | no LLM rerun |
| `overclaim_count` (RPP-EMP B mean)     |  1.90 |   n/a | no LLM rerun |
| `useful_objection_count` (ABL B_PRO mean) | 2.10 | n/a | no LLM rerun |
| `false_objection_count` (ABL B_PRO mean)  | 0.00 | n/a | no LLM rerun |
| `synthesis_degradation_count` (ABL B_PRO mean) | 5.60 | n/a | no LLM rerun |
| Runtime cost estimate               | 0 USD  | 0 USD | 0 |

### Per-trajectory Phase V span change

```
                       BEFORE         AFTER       terminal_failure
adv01    V loops 3..5         3..5        ATTRACTOR_LOCK
adv03    V loops 2..5         2..5        ATTRACTOR_LOCK   (preserved by terminal-failure guard)
adv06    V loops 4..6         4..6        ATTRACTOR_LOCK
adv07    V loops 5..5         5..5        GRAPH_TOO_LARGE  (terminal-failure-only branch unchanged)
adv08    V loops 5..6         5..6        NOVELTY_COLLAPSE
adv09    V loops 2..8     ->  2..5        None             <-- closed on reversal
adv10    V loops 6..7         6..7        None             (only 1 broken loop after trigger; no closure)
```

Net change: 1 trajectory (adv09). Effect: Phase V no longer claims
the recovery region (loops 6..8).

## DET-FAL false-positive accounting

DET-FAL listed 4 false positives across the 10-trajectory adversarial
set:

1. **T5 Phase II declared on healthy oscillating trajectory** — still
   present.
2. **T6 Penultimate-EN candidate=True for non-transformative EN** —
   still present.
3. **T9 Phase III ∧ Phase V overlap with no disclaimer** — **resolved**
   by this cycle. Phase V on adv09 now ends at loop 5; Phase III on
   adv09 still runs loops 6..8, but they no longer overlap.
4. **T10 Phase II span bug** — resolved by cycle 1.

`false_positive_count` is now 2 (T5, T6). Cycle 1 + cycle 2 together
have halved the FP count (4 → 2).

## Regressions

None on the n=10 adversarial set. The first implementation regressed
adv03 (`V loops 2..5` → `V loops 2..2`); the accepted implementation
restores adv03 via the `has_terminal_failure` guard.

## Unexpected effects

- The proposal predicted "only adv09 changes". Initial impl changed
  both adv09 and adv03; the terminal-failure guard restored adv03.
  This is exactly the kind of failed-attempt material the strict rule
  set requires us to preserve — recorded above.

## Verdict

**ACCEPTED.**

- DET-FAL `false_positive_count` 4 → 2 (one FP resolved this cycle;
  one resolved in cycle 1).
- No DET-FAL false negative introduced (5 → 5).
- 15/15 pytest cases pass.
- adv03 preserved.

## Next-cycle hint (DESi self-diagnosis pointer)

Per `paper0/self_reflection.md §4.3 + §6.3`, the next pure-detector
target is **`detect_saturation_without_en`** (closes DET-FAL T8:
Phase II is EN-gated, so trajectories with novelty collapse but no EN
events never enter Phase II). Cycle 3 candidate.
