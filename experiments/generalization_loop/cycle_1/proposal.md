# Cycle 1 — Tighten `detect_terminal_attractor_subjects` with a tail-saturation guard

## DESi self-diagnosis (from baseline)

`outputs/generalization_loop/baseline_metrics.json` shows
`attractor_lock` firing on **20/20** generalization fixtures and **9/10**
original adversarial fixtures. The detector currently returns a
candidate whenever `focus_claim_id` is repeated >= 2× in the tail of 3
steps, regardless of whether the tail actually *looks* like an attractor
(low novelty, elevated duplication).

Because DES trajectories typically maintain `focus_claim_id` continuity
during normal exploration, the current heuristic is essentially
"the trajectory has at least 2 well-formed tail steps", which is too
weak to mean anything.

## Change (one detector only — strict rule 1 honoured)

`detect_terminal_attractor_subjects` adds a **tail-saturation guard**:

```
mean_novel_tail = mean(step.novel_claims for step in tail)
mean_dup_tail   = mean(step.dup_rate     for step in tail)
saturated = (mean_novel_tail <= 3.0) and (mean_dup_tail >= 0.30)
```

If `saturated` is False, `candidate_claim_ids = []` regardless of
focus/presence repetition. If True, the existing repetition logic
runs unchanged.

Thresholds chosen to be intentionally LOOSE (looser than Phase V's
`dup >= 0.50` and `novel <= 1`), so the detector still fires on borderline
attractors. The point is to suppress firings on trajectories that are
clearly still exploring (mean novel > 3 in the tail).

Rejected alternatives:
- "Require all tail focus_claim_ids equal" — too strict; would suppress
  real attractors that flicker focus once.
- "Use Phase V trigger as gate" — couples two detectors; cycle 1 wants
  ONE change.
- "Drop the detector entirely" — loses real signal on adv09, adv01.

## Predicted impact

- n=20 suite: `attractor_lock` fire count 20 → ~5 (only gen07, gen15,
  and the few fixtures with genuine saturation tails).
- n=10 suite: `attractor_lock` fire count 9 → ~6-7 (preserves adv01,
  adv04, adv08, adv09, adv10; suppresses adv03/adv06/adv05 where
  tail is not saturated).
- No DET-FAL counter change expected (DET-FAL ledger doesn't depend
  on attractor candidates).
- One new regression test asserts the guard.

## Risk

If the guard's thresholds are wrong (too strict), we'll suppress
real attractor signal on edge cases. The cycle-1 evaluation will
verify on both suites; if regressed, cycle 2 will widen thresholds
(or, per strict-rule 4, revert and document the failure).
