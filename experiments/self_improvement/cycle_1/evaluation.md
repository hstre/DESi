# Cycle 1 evaluation — fix malformed phase span invariant

## Tests

| Suite | Before | After |
|---|---|---|
| pytest (all) | 13 passed | **14 passed** (one regression test added) |
| New test `test_phase_ii_span_is_well_ordered` | failed (asserts `3 <= 2`) | passes |

The regression test was added *first* and confirmed to fail on the
pre-cycle codebase (`git stash push -- src/desi/phase_detector.py` →
`pytest` → AssertionError quoting the malformed span). The fix was
then applied, and the test passes.

## Primary-metrics table (before/after)

Measured by running `detect_phases()` on all 10 adversarial
trajectories in `data/adversarial/*.json` and counting phase spans
where `start_loop > end_loop` (`malformed_phase_span_count`) and known
behavioural false-positive / false-negative cases per the DET-FAL
ledger. Other metrics either are computed only by the LLM-side
role-policy harness (not re-run this cycle — no prompt change) or are
deterministic and unchanged by this fix.

| Metric                               | Before | After | Delta |
|--------------------------------------|-------:|------:|------:|
| `malformed_phase_span_count`         |      1 |  **0** |  −1 |
| `false_positive_count` (DET-FAL)     |      4 |     4 |   0 |
| `false_negative_count` (DET-FAL)     |      5 |     5 |   0 |
| `phase_overlap_count` (RPP-EMP B mean) |   0.20 |   n/a |  no LLM rerun |
| `unsupported_claims` (RPP-EMP B mean) |   2.80 |  n/a |  no LLM rerun |
| `hallucinated_causal_claims` (RPP-EMP B mean) | 2.30 | n/a | no LLM rerun |
| `overclaim_count` (RPP-EMP B mean)    |   1.90 |  n/a |  no LLM rerun |
| `useful_objection_count` (ABL B_PRO mean) | 2.10 | n/a |  no LLM rerun |
| `false_objection_count` (ABL B_PRO mean)  | 0.00 | n/a |  no LLM rerun |
| `synthesis_degradation_count` (ABL B_PRO mean) | 5.60 | n/a | no LLM rerun |
| Runtime cost estimate                | 0 USD  | 0 USD | 0 |

### Per-trajectory phase spans (after fix)

```
adv01: I:0..0, II:1..1, V:3..5
adv02: I:0..0, II:1..2
adv03: I:0..0, II:1..2, V:2..5
adv04: I:0..0
adv05: I:0..0, II:1..1, III:2..2
adv06: I:0..0, II:1..1, III:2..2, V:4..6
adv07: I:0..0, V:5..5
adv08: I:0..0, V:5..6
adv09: I:0..0, II:2..2, III:6..8, IV:2..4, V:2..8
adv10: I:0..0, II:2..3, III:3..5, V:6..7
```

adv10 Phase II is now `loops 2..3` (well-ordered) where it was `3..2`
before. All other phase spans are bit-for-bit identical to the
pre-cycle output.

## Regressions

None observed. The fix touches exactly one phase span on one
trajectory (adv10) and reorients its bounds without changing the
trigger evidence, the confidence label, or any other phase on any
other trajectory.

## Unexpected effects

None. The proposal predicted "all 13 existing pytest cases must still
pass" — confirmed (now 14 with the regression).

## Verdict

**ACCEPTED.**

- The primary metric (`malformed_phase_span_count`) improved by 1
  (100% reduction on the n=10 sample).
- No other metric regressed.
- The fix is single-line and localised.

## What this cycle does NOT show

- Whether real-world DES trajectories (paper7+) contain other
  ordering shapes that produce malformed spans in detectors *other*
  than Phase II. The fix is local to `detect_phase_ii`; the four
  other phase detectors are unchanged.
- Whether the LLM-side role outputs for adv10 will narrate the
  Phase II span correctly under the corrected boundary order. Not
  re-tested this cycle (no prompt change).

## Next-cycle hint (DESi self-diagnosis pointer)

Per `paper0/self_reflection.md §4.4 + §6.4`, the next highest-leverage
deterministic fix is the Phase V reversal logic (T9-shape:
Phase V fires at loop 2 and never reconsiders after a late recovery).
That is a strict superset-of-scope candidate for cycle 2.
