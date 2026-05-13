# Cycle 2 evaluation — dup_delta = -0.08 with high ENI and strong novelty rebound

## Probe output (verbatim)

```
trajectory_id: fx2_high_eni_partial_dup_recovery
n_en_events: 1
composite_labels: ["genuine_transformation_unconfirmed"]
novelty_recoveries: [{loop: 2, dup_delta: -0.07999999999999996,
                      novel_next: 6, recovered: false}]
phase_iii_present: false
phase_iii_span: null
confirmed_count: 0
birth_B: 0
```

## Verdict: **FALSIFIED**

`birth(B) = 0` on a trajectory with eni = 0.18 (clearly in the high
band) and a recovery that any human reader would call real:
6 novel claims next loop, 8% drop in duplication rate, sustained
recovery for 3 subsequent loops (dup 0.42 → 0.34 → 0.28 → 0.22).
DESi's gate says no.

## Discussion

Two distinct problems converge:

1. **The recovery threshold (-0.10) is calibrated against the n=10
   adversarial suite.** That suite always had big-step recoveries
   (dup drops ≥ 0.20). The threshold was never stress-tested on
   "real but gradual" recoveries. -0.08 is well within plausible
   single-step recovery rates from real DES runs.

2. **Float-comparison fragility.** The actual `dup_delta` computed
   here is `-0.07999999999999996` (the result of `0.34 - 0.42` in
   IEEE 754). Even setting `dup_after = 0.32` (clean -0.10 by
   intent) might produce -0.09999999999999998 and fail the
   `<= -0.10` gate. The threshold needs tolerance.

The downstream consequence is identical to cycle 1: the composite
classifier labels this `genuine_transformation_unconfirmed` and
the Phase III gate does not fire.

## Note on `_unconfirmed` semantics

Pre-cycle-7 (self-improvement loop), this trajectory would have
been called `genuine_transformation` (legacy classifier sees
eni > 0.12). Cycle 7's composite distinction sharpened the
recovery requirement. The cycle was correct (it filtered adv06's
no-recovery high-ENI from being a birth), but the threshold for
"recovered" was not re-tuned. A reasonable real DES recovery is
now sub-threshold.

## Marginal epistemic gain

**Non-zero.** A second, independent boundary forces birth(B) = 0
on a Paper-0-plausible trajectory.

## Stop or continue?

**Continue.** Two threshold failures so far. Test Phase III's
per-loop recovery rule next.
