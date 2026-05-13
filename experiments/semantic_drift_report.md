# Semantic-Drift Audit Report

**Date**: 2026-05-13
**Triggering instruction**: user task "falsify birth(B). Paper 0 may be wrong."
**Branch**: `experiment/desi-birth-falsification` (the branch name itself
carries the original mislabel; preserved on remote for audit).

This report documents a category-level semantic error I introduced.
It was caught and called out by the user. This document does the
post-mortem the user asked for.

---

## What Paper 0 defines

```
birth(B) = (D, R, F, P, ΔQ)
```

A **5-tuple** structural definition. Paper 0 is not in this repository
(`grep -rn "birth(B)\|(D, R, F, P\|ΔQ"` over the entire tree returns
ZERO hits prior to the misnamed artifact). I had no access to the
component definitions of D, R, F, P, or ΔQ at the moment I undertook
the task.

## What I substituted

```
birth(B) = 1 iff classify_en_event_composite produces any label
            == "genuine_transformation_confirmed"
```

A **single-bit boolean** over the output of one DESi classifier. The
substitution discarded:

- **D** — silently dropped.
- **R** — silently dropped.
- **F** — silently dropped.
- **P** — partially conflated with Phase III in cycle 3, but Phase III
  is not the same as "P" without a Paper-0 mapping I never built.
- **ΔQ** — silently dropped; no quality-delta metric was even
  consulted.

A 5-tuple → 1-bit projection. Four dimensions were silently zeroed.

## Where the drift occurred

Single point of failure: my reasoning step **before** writing
`experiments/birth_falsification/probe.py`. The transcript shows me
identifying:

> "birth(B) likely refers to something specific in the DES/DESi paper.
> Without more context, I need to make a reasonable interpretation."

I then chose to "operationalize" the term by picking the DESi composite
classifier label that *sounded most analogous* to "birth" —
`genuine_transformation_confirmed`. This choice was based on:

- A label name that includes "genuine" and "confirmed" — superficially
  reads as a positive declaration of something happening.
- The fact that this label gates Phase III's first trigger, which I
  rationalised as "the birth-detection signal".

Both of those are surface analogies. Neither is a Paper-0-derived
mapping. The choice was made **without consulting any source for the
actual definition** and without **asking the user** what `birth(B)`
referred to. Both options were available; I took neither.

## How the drift propagated

The substitution was baked into three places, then inherited
everywhere:

1. **`probe.py`** — return-key `birth_B` and operational definition in
   the docstring.
2. **`README.md`** — explicit "Operational definition" block.
3. **Each `cycle_N/proposal.md`** — used `birth(B)` as the falsification
   target without re-checking the definition.

Once those three files claimed the boolean interpretation, all four
cycles ran against the wrong target. The artefacts of those cycles
contain real findings — three actual boundary-behavior failures in
`classify_en_event_composite` and `_clip_phase_overlaps` — but those
findings are **not falsifications of birth(B)**. They are
falsifications of a name I gave to a single composite label.

## What the falsified target actually was

The four cycles probed the boundary behavior of:

- the strict-greater comparison in `classify_en_event_composite`'s
  bucket selection (cycle 1);
- the `dup_delta <= -0.10` cutoff in `compute_novelty_recovery` (cycle 2);
- `_clip_phase_overlaps` interaction with `terminal_failure_mode`
  (cycle 3); and
- phantom keys in `experiments/generalization_loop/evaluate_suite.py`
  (cycle 4).

These are real DESi findings worth keeping. They concern the
**composite EN label** classifier and adjacent phase-detection logic.
Hence the directory rename to
`experiments/composite_en_label_falsification/`.

They are **not** findings about Paper 0's birth(B) tuple. We do not
know — from anything in this repo — whether DESi can detect
`(D, R, F, P, ΔQ)` correctly, whether any of the five components are
even representable in DESi's metric stack, or whether birth(B) can be
forced to 0 by any input. Those questions remain open.

## What should have happened

Before writing the probe, I should have done one of:

1. **Asked the user** what the components of `birth(B)` map to in
   DESi-side data. `AskUserQuestion` is available for exactly this.
2. **Searched the repository** for the tuple-form definition. (I did
   this *after* the user's correction; I should have done it *before*.)
3. **Surfaced the ambiguity** in the first response: "I cannot find
   Paper 0's `birth(B)` definition in the repository; before probing
   I need either the definition or your confirmation of an operational
   proxy."

I did none of these. The fastest available action — pick a label and
go — won.

## What is being corrected in this commit

- The directory `experiments/birth_falsification/` is renamed to
  `experiments/composite_en_label_falsification/` to reflect what the
  cycles actually probed.
- The internal references to `birth(B)` inside the renamed directory
  are tagged as the mislabelled term, with a pointer back to this
  drift report.
- This `semantic_drift_report.md` is added at the
  `experiments/` top level.
- The probe-return field `birth_B` is renamed to `confirmed_genuine_en`.

DESi source under `src/desi/` is **NOT** modified.

## What is preserved

Per the user's "preserve every failed hypothesis" rule from the prior
loop, the four cycles' artefacts are kept verbatim other than the
`birth(B)` → `confirmed_genuine_en` term-level corrections. The
mislabelled framing is part of the historical record. This report
documents the failure of the framing.

## What is still owed

A real attempt to falsify Paper 0's `birth(B) = (D, R, F, P, ΔQ)`
requires Paper 0's definitions of D, R, F, P, ΔQ. Without those,
nothing in this repository's metric stack can be honestly mapped to
the tuple. The next step — if the user wants to continue this line —
is the user providing those component definitions (or pointing to the
section of Paper 0 that contains them).

I will not attempt another operational definition without that input.
