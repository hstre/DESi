# Cycle 1 evaluation — eni=0.12 exactly with strong recovery

## Probe output (verbatim)

```
trajectory_id: fx1_eni_eq_high_threshold_with_recovery
n_en_events: 1
composite_labels: ["borderline_with_recovery"]
novelty_recoveries: [{loop: 2, dup_delta: -0.2, novel_next: 5, recovered: true}]
phase_iii_present: false
phase_iii_span: null
confirmed_count: 0
birth_B: 0
```

## Verdict: **FALSIFIED**

`birth(B) = 0` was forced on a trajectory whose only EN event sits at
the documented high-ENI threshold (0.12) and whose recovery is
unambiguous (5 novel claims, dup_delta = -0.20). The `recovered` flag
correctly fires; the composite classifier downgrades the event to
`borderline_with_recovery` because of the strict-greater comparison.

## Discussion

This is a **specification-vs-implementation mismatch** at the
high-threshold boundary:

- Paper 0 documents the bimodal classifier with the constants
  `ENI_LOW_THRESHOLD = 0.10` and `ENI_HIGH_THRESHOLD = 0.12`. A
  reasonable reading is that `eni == 0.12` is "high".
- `classify_en_event_composite` (and `classify_en_event`) uses
  `eni > ENI_HIGH_THRESHOLD`. The threshold value itself is
  excluded from the high bucket.

DES's ENI computation produces continuous floats. The probability of
ever hitting **exactly** 0.12 is small, but the boundary asymmetry
also affects values like 0.12000000000000001 vs 0.12 in
floating-point arithmetic. A trajectory whose DES-side ENI rounds
to 0.12 (e.g. via single-precision intermediate, or
explicit-quantisation) would be invisible to birth detection.

The symmetric issue exists at the low threshold (`eni < 0.10` ⇒
"low"; eni == 0.10 ⇒ "borderline"); not falsifying here since
eni = 0.10 is not a birth candidate anyway.

## Marginal epistemic gain

**Non-zero.** This is a real specification mismatch and a reachable
failure on real-valued ENI. Recommend a paper0 follow-up:
"the bimodal classifier's boundary inclusion should match the paper
text; choose one of: change implementation to `>=` / `<=`, or
change paper to specify open intervals". Either is fine; the
asymmetry between text and code is the bug.

## Stop or continue?

**Continue.** This was one boundary; explore others (recovery
threshold, Phase III recovery threshold, phase-clip suppression).
