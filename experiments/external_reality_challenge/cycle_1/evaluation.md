# Cycle 1 — Conservative translation of upstream DES → DESi

## Input

`source/des_state.json` from `hstre/DES` (upstream main, fetched fresh
on this branch). Translated via `translator.py --mode conservative`:
35 steps from `operation_history`, all DESi-side metrics
(`novel_claims`, `dup_rate`, `claims[]`, `en_events[]`) left at their
identity values because upstream DES does not emit them.

## DESi probe output

```
trajectory_id:        des_upstream_state_conservative
n_en_events:          0
composite_labels:     []
phase_iii_present:    False
confirmed_genuine_en: 0

phases detected:
  I_EXPOSITION (0–0, medium)
  II_FIRST_SATURATION_MODULATION (1–1, low)

aggregator detectors:
  attractor_lock:           False (tail not saturated)
  branch_explosion:         False
  mild_stagnation:          False
  step_coherence_violation: TRUE — 34 of 35 steps flagged
  borderline_chain:         False
  penultimate_en_candidate: False
```

## Three failures observed

### Failure 1: Phase I fires by accident on a null trajectory

Phase I's three conditions are (a) novel_claims ≥ 10, (b) dup_rate <
0.30, (c) no EN at loop 0. The conservative translation has
novel_claims = 0 (fails a), dup_rate = 0 (passes b), no EN (passes c).
2-of-3 conditions are satisfied → "medium confidence Phase I".

This is wrong. The 2 passing conditions both pass *because the data
is missing*. DESi has no way to distinguish "DES emitted dup_rate of
0" from "DESi was not given a dup_rate". A null trajectory should not
produce a Phase I diagnosis at all.

### Failure 2: Phase II fires by spurious persistence

`detect_phase_ii` requires `novel_claims ≤ 2 on two consecutive
loops`. All steps have novel_claims = 0, so this condition is met
on loops 1 and 2 → Phase II is emitted. Same root cause: missing
data masquerades as saturation.

### Failure 3 (the main one): `step_coherence` fires on 34 of 35 steps

DESi's `validate_step_metric_coherence` (added in self-improvement
cycle 6) catches "impossible" combinations. One of those is
`dup_rate < 0.05 AND novel_claims = 0 after loop 0`. The
conservative translation sets BOTH to 0 for every step, so the rule
fires for every step from loop 1 onward.

The label of the rule is "incoherent step" — implying the data is
self-contradictory. The data is not self-contradictory; it is
**absent**. DESi conflates "missing field" with "contradictory field".

## What an honest external-reality reader would conclude

Reading DESi's report on this conservative translation, a reader who
did not know the translator's behaviour would conclude:

> "Real DES output is full of incoherent steps, except for an
> ambiguous Phase I + Phase II at the start."

The truth is:

> "Upstream DES produces 35 well-formed operator-on-claim events. The
> input does not include the DESi-side novelty/duplication metrics
> because upstream DES has no such measurement loop. DESi has no
> detector for 'schema mismatch' and reports schema gaps as semantic
> incoherence."

## Verdict

DESi is **mute or actively misleading** on real DES output via the
conservative translation. The mute case (no birth-signal) is
honest; the misleading case (`step_coherence` firing as if the data
contradicted itself) is not.

Two of DESi's accepted-cycle additions trigger spuriously on this
data:

- self-improvement cycle 6 (`validate_step_metric_coherence`):
  flags 34/35 steps as incoherent. **Cycle 6's rule does not
  distinguish missing data from contradictory data.**
- gen-cycle 5 (`detect_borderline_chain`): no fires (no EN events
  to chain). Silent — fine.

## Implication for birth(B) §12.1

This is evidence relevant to component **ΔQ**. The cited ΔQ > 0 in
Paper 0 §12.2 was measured on in-distribution suites. On the first
piece of out-of-distribution data presented to DESi, the dominant
diagnostic output is a single detector firing on 34/35 steps with a
misleading label. **There is no measurable improvement of behaviour
on this distribution.**

Under the strong reading of ΔQ ("measurable improvement on a
distribution authored independent of DESi development"), ΔQ = 0 here.
By the disjunctive rule birth(B) = 0.

Paper 0 §12.3 itself acknowledged this lower-bound limit. The
challenge confirms it empirically.
