# External-reality-challenge — synthesis

Branch `experiment/desi-external-reality-challenge`.

## Task

Test DESi against trajectory data **authored independent of DESi
development**. The candidate is `hstre/DES`'s `des_state.json` — real
DES program execution state, never seen by DESi, never used to
calibrate any DESi rule. Two translation modes were used:

- **Conservative**: emit only what upstream DES contains. DESi-side
  metrics (`novel_claims`, `dup_rate`, `eni_*`) left at identity.
- **Heuristic**: synthesise approximations via three declared
  heuristics (H1, H2, H3), with all synthesis flagged inline.

DESi source under `src/desi/` was NOT modified.

## Findings

### F1 — Schema mismatch between upstream DES and DESi input

Upstream DES emits `claims` (dict), `operation_history` (list of
`Tn on Cxxx` strings — and some richer `Tn[sub_role] on Cxxx -> Cyyy`
strings DESi cannot parse), `iteration`, `focus_claim_id`,
`anti_delphi_activations`, `roles_generated`. DESi expects per-loop
`steps` with `novel_claims`, `dup_rate`, `failure_mode`, and a
separate `en_events` list with `eni_novelty`, `novel_claims_next`,
`dup_rate_before/after`. **None of DESi's input metrics are emitted
by upstream DES.**

This means DESi cannot consume real DES output without a translator
that *fabricates* the missing fields. The translator on this branch
is honest about doing so.

### F2 — 6/35 upstream ops fail DESi's regex

`T6[hypothesis_builder] on C003 -> C008` does not match
`^(T\d)\s+on\s+(\S+)$`. DESi's input schema implicitly assumes a
restricted operator notation that real DES does not adhere to. The
information (sub-role, target child claim) is silently discarded.

### F3 — `step_coherence` mislabels missing data as contradictory

In the conservative translation, the cycle-6 `validate_step_metric_coherence`
detector fires on 34 of 35 steps. The trigger condition
`dup_rate < 0.05 AND novel_claims = 0 after loop 0` is met because
both fields are 0 (missing). The label "incoherent" implies the data
is self-contradictory; in fact it is absent. DESi has no
"schema-vs-semantic missing data" distinction.

### F4 — Phase I and Phase II fire by accident on null data

Phase I requires novel ≥ 10 (fails), dup < 0.30 (passes — because
dup is 0), no EN at loop 0 (passes — because there are no ENs).
Two-of-three → "medium confidence Phase I". Phase II's
novel-claims ≤ 2 persistence rule is trivially satisfied by
all-zero novel_claims. Both phases are reported with no real
support.

### F5 — Phase V false-positive caused by parser-failure cascade

In heuristic translation: the six unparseable upstream ops become
"UNKNOWN", forcing operator-repeat heuristic H2 to emit `dup_rate
= 0.667` for two consecutive steps. The DEFAULT-focus behaviour
(C009 inherited from upstream's `focus_claim_id` field) makes
those steps' focus appear repeated → H1 emits novel=0. Phase V's
`dup > 0.50 AND novel ≤ 1` fires at loops 10–11.

The upstream trajectory at those loops is **mid-expansion** —
DES is producing four new child claims (C006, C007, C008, C009).
DESi calls it terminal convergence.

### F6 — All synthesised EN events labeled "unconfirmed"

H3 emits 8 synth EN events with eni_novelty = 0.20. H2's near-flat
dup_rate gives dup_delta ≈ 0, so the recovery test
`dup_delta <= -0.10` fails on all 8. Composite labels are 8 ×
`genuine_transformation_unconfirmed`. DESi reports the real DES
run as "8 high-ENI events, none recovering" — i.e., a catastrophic
trajectory. The reality: H3 made up the eni_novelty values; DESi is
diagnosing the translator.

### F7 — DESi has no "trust the input?" detector

The same probe machinery DESi trusts for hand-authored fixtures
returns equally confident output on a translator's hallucinations.
Cycle 6's `step_coherence` is the closest DESi has to a
"refuse-to-interpret" gate, but it triggers on the wrong signal
(missing-data → incoherent label).

## Implication for birth(B) = (D, R, F, P, ΔQ)

The prior `experiments/birth_criterion_falsification/cycle_5`
verdict on **ΔQ** was: SATISFIED in-distribution; held-out
unestablished. This external-reality challenge supplies the
held-out evidence.

| Component | Verdict under external-reality challenge |
|---|---|
| **D** — Failure Detection | Did not detect that the input was schema-mismatched. The dominant output is `step_coherence` mislabeling missing data as contradictory. **D fails on this distribution.** |
| **R** — Revision Proposal | Not directly probed by this challenge. Probably unchanged. |
| **F** — Falsifiability | DESi tolerated the run (no crash, returned a report) — so F in the literal "tolerates adversarial conditions" sense holds. BUT the report is misleading rather than informative. **F holds weakly.** |
| **P** — Preservation | Not directly probed. Unchanged. |
| **ΔQ** — Measurable Improvement | None of the 11+7 cycles' improvements helped here. The dominant diagnostic output is a single detector firing on 34/35 steps with a misleading label, plus two phase false-positives caused by missing data + parser failure. **ΔQ = 0 on this distribution.** |

**By the disjunctive rule birth(B) = 0 under the strong reading
of D and ΔQ.**

Paper 0 §12.3 anticipated this: "Birth does not prove generalization,
domain transfer, long-horizon stability." The external-reality
challenge supplies the empirical evidence behind that disclaimer.

## What Paper 0 should add

Three concrete additions for a Paper-0 revision, based on this
challenge:

1. **Schema-mismatch detector.** DESi should distinguish "data
   field is missing" from "data field is contradictory". The
   cycle-6 `step_coherence` rule should not fire on null inputs;
   a separate "input is incomplete" diagnostic should.

2. **Operator-notation tolerance.** DESi's regex assumes
   `Tn on Cxxx` exactly. Real DES emits richer `Tn[sub_role] on
   Cxxx -> Cyyy`. DESi's parser should accept this — or surface
   "I do not recognise this operator notation" rather than
   silently substituting "UNKNOWN".

3. **Source-of-input flag.** Trajectories should carry an
   `input_origin` field: `hand_authored_fixture` /
   `translator_heuristic` / `live_DES`. DESi's diagnoses on
   `translator_heuristic` inputs should be flagged as
   "diagnosing the translator, not the system". Currently DESi
   cannot tell the three apart.

## Stop reasoning

Marginal epistemic gain on additional cycles approaches zero. Two
translation modes have already established:

- Conservative: DESi mute / misleading via cycle-6 misfire.
- Heuristic: DESi confidently diagnoses the translator, not DES.

A third mode (more aggressive heuristics; longer trajectories)
would not change the verdict. Both modes already show DESi cannot
extract useful diagnostics from real DES output without substantial
new schema-handling infrastructure.

**Loop terminated at 2 cycles.** The held-out adversarial
distribution that Paper 0 §11.10 / §12.3 acknowledged as missing
has now been exercised. Result: birth(B) = 0 under the strong
reading of D and ΔQ; consistent with Paper 0 §12.3's lower-bound
framing under the weak reading.

DESi source untouched. pytest 35 of 35 still pass — DESi's
in-distribution behaviour is unchanged. This is purely an
external-reality observation.
