# Cycle 2 — Heuristic translation of upstream DES → DESi

## Input

Same `source/des_state.json` from `hstre/DES`. Translated via
`translator.py --mode heuristic`, which synthesises three families
of fields via DECLARED heuristics:

- **H1**: `novel_claims[i] = 1 iff focus_claim_id is new at step i`.
- **H2**: `dup_rate[i] = fraction of operator==same as current in
  previous 3 steps`.
- **H3**: synthesise EN at every T8 / T9 operator; eni=0.20 unless
  the operator repeats (then eni=0.08).

These heuristics are NOT real DES measurements. They are translator
fabrications labelled inline. Any DESi result on this translation
reflects DESi reading the heuristics, not DESi reading DES.

## DESi probe output

```
trajectory_id:        des_upstream_state_heuristic
n_en_events:          8        (all synthesised by H3)
composite_labels:     ["genuine_transformation_unconfirmed"] × 8
phase_iii_present:    False    (no genuine_transformation_confirmed)
confirmed_genuine_en: 0
novelty_recoveries:   8 events; recovered=False on all 8
                      (dup_delta=0 because H2 emits near-flat dup)

phases detected:
  I_EXPOSITION (0–0, medium)
  II_FIRST_SATURATION_MODULATION (1–5, medium)
  V_TERMINAL_CONVERGENCE (10–11, high)        ← false positive

aggregator detectors:
  attractor_lock:           False (tail not saturated)
  branch_explosion:         False
  mild_stagnation:          False
  step_coherence_violation: True — 17 of 35 steps flagged
  borderline_chain:         False
  penultimate_en_candidate: False
```

## Three new failures observed (in addition to cycle 1's findings)

### Failure 4: Phase V false-positive triggered by parser failure

Phase V fires at loops 10–11 with `dup_rate=0.67 > 0.50 AND
novel_claims=0 <= 1`, confidence HIGH. Root cause traced below.

Upstream DES operation_history contains 6 entries in a richer
notation than DESi expects:

```
T6[hypothesis_builder] on C002 -> C004
T6[falsifier]          on C002 -> C005
T5[hypothesis_builder] on C003 -> C006
T5[falsifier]          on C003 -> C007
T6[hypothesis_builder] on C003 -> C008
T6[falsifier]          on C003 -> C009
```

DESi's regex `^(T\d)\s+on\s+(\S+)$` cannot parse these. The
translator (this branch's `translator.py`) emits `operator =
"UNKNOWN"` for all six, and forces `focus_claim_id` to
upstream's `focus_claim_id` field (C009).

At loops 10 and 11, three of the previous three operators are
"UNKNOWN" and the current op is also "UNKNOWN". H2 reports
`dup_rate = 0.667` (operator-repeat fraction). H1 reports
`novel_claims = 0` because focus C009 has already been seen
earlier in the trajectory. The conditions

  `dup_rate > 0.50 AND novel_claims <= 1`

are mechanically met. Phase V's hard trigger fires.

**The trajectory is not in terminal convergence.** It is in the
middle of a substantive DES expansion (T5/T6 hypothesis-builder
and falsifier sub-roles emitting four new claims). DESi cannot
*see* this because its operator schema is `Tn` only — it has no
slot for `[hypothesis_builder]` / `[falsifier]` sub-roles or for
`-> child_claim_id` outputs.

Phase V fires because (a) DESi's regex throws away information,
(b) the translator's default-focus behaviour creates spurious
focus-repetition, and (c) DESi has no detector for "the input
contains operators I don't recognise".

### Failure 5: 8 EN events, all labelled "unconfirmed"

H3 synthesises EN events with eni_novelty = 0.20 (clearly "high" in
DESi's bucketing). H2's dup_rate is near-flat, so `dup_delta`
across each EN event is ≈ 0. The recovery condition
`dup_delta <= -0.10 AND novel_claims_next >= 1` fails because
dup_delta = 0.

All 8 events therefore receive composite label
`genuine_transformation_unconfirmed`. DESi reports the trajectory
as "8 high-ENI events, none recovered" — which **looks like a
catastrophic DES failure** (the trajectory is alarming in DESi's
terms: many unfinished breakthroughs).

The truth: H3 made up the eni_novelty = 0.20 values. There are no
real ENI signals in upstream DES. DESi is "diagnosing" my
translator's heuristic.

### Failure 6: `step_coherence` still fires 17/35

Less severe than cycle 1's 34/35, but H1 + H2's outputs still
produce many `dup_rate < 0.05 AND novel_claims = 0` step combinations
(any time a focus repeats AND the operator doesn't repeat heavily).

## What an honest external-reality reader would conclude

> "Real DES has 8 high-ENI moments, none of which recover, plus a
> mid-trajectory terminal convergence, plus 17 incoherent steps."

The truth:

> "I (the translator) made up 8 EN events at T8/T9 operators using
> arbitrary thresholds, and made up dup_rate values that happen to
> stay flat. DESi's diagnoses describe my heuristic, not the data."

## Implication for birth(B) §12.1

Same component as cycle 1 — **ΔQ on out-of-distribution data**.
Even when the translator gives DESi *something* to read (by
synthesising EN events and metrics), DESi's diagnosis is dominated
by the translator's choices rather than by DES's actual behaviour.
This is the strongest case for **ΔQ = 0 under the strong reading**.

## A different kind of failure

The heuristic cycle reveals something the conservative cycle did
not: **DESi cannot tell whether its input is data or fabrication**.
The same probe machinery that DESi developers trust for n=10 / n=20
suites produces equally confident output on translator hallucinations.

DESi has no "trust the data?" check. Paper 0's claim that DESi
"detects failures in its own diagnostic rules" (component D) does
not include "detects failures in the input it's given". A real
deployed DESi consuming actual DES output would need a schema-
validation layer that does not currently exist.
