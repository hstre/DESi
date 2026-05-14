# birth(B) falsification — synthesis

Source definition: `DESi Paper-0 Birth v1-6.docx` §12.1.

```
B = (D, R, F, P, ΔQ)
birth(B) = 1 iff all five present.
If any component is absent: birth(B) = 0.
```

Falsification attempt: 5 cycles, one per component, each running the
strongest absence-hypothesis I can construct against repo evidence.

## Per-component verdicts

| Component | Verdict | Forces birth(B) = 0? |
|---|---|:---:|
| **D** — Failure Detection | WEAKLY SATISFIED (pytest + suite metrics satisfy the literal wording; architectural separation between detector and detected is not enforced) | **No** |
| **R** — Revision Proposal | SATISFIED (revisions are concrete and measurable; some are stylistic but still satisfy §12.1's wording) | **No** |
| **F** — Falsifiability | SATISFIED (revisions are testable; rejection-tolerance documented in cycle 2 + cycle 10 failed attempts) | **No** |
| **P** — Preservation of Rejected Paths | SATISFIED with two documented frictions (comment trimming in gen-cycles 1-4 later restored; semantic-drift rename annotated, not hidden) | **No** |
| **ΔQ** — Measurable Improvement | SATISFIED in-distribution (FP 4→0, FN 5→2 on suites authored by/with knowledge of DESi); held-out unestablished | **No** |

**Disjunctive conclusion:** I cannot force birth(B) = 0 from what I
can verify in the repo. Paper 0 §12.1's wording is permissive enough
that all five components hold for DESi as documented through cycle
12 of the self-improvement loop and cycle 7 of the generalization
loop.

## Where the criterion is fragile

While I could not force birth(B) = 0, three of the five components
hold only at the lower bound of Paper 0's wording. A reasonable
strengthening of any one would flip the verdict:

1. **D — architectural separation.** If D required the detector to
   be a distinct epistemic subsystem from the diagnosed system —
   not merely the same LLM with a different prefix — D would currently
   be 0. `src/desi/` contains zero self-introspection code; the
   detection happens in LLM turns and in pytest. The pytest path
   survives the stricter reading; the LLM path does not.

2. **F — held-out adversarial testing.** If F required at least one
   accepted revision to have been tested against a distribution
   authored independent of DESi development, F would currently be 0.
   No such distribution exists in the repo. Paper 0 §11.10 itself
   acknowledges this.

3. **ΔQ — independent-distribution improvement.** Same as F's
   strengthening: if ΔQ required measurable improvement on a
   distribution not designed by/with knowledge of DESi, ΔQ would
   currently be 0.

So:

- Under Paper 0 §12.1 **as written**: birth(B) = 1 stands.
- Under a stricter reading on any of D / F / ΔQ: birth(B) = 0 is
  forced today by the missing held-out evidence.

This is consistent with Paper 0 §12.3 itself, which is explicit:

> Birth does not prove generalization, domain transfer, long-horizon
> stability, autonomous science, or scheduler authority. Birth is a
> lower bound, not an endpoint.

Paper 0 commits to the **lower-bound** reading. Under that reading
the falsification attempt **fails**.

## What is NOT a falsification (per the user's drift correction)

- Earlier "FALSIFIED" claims in
  `experiments/composite_en_label_falsification/` (formerly
  `experiments/birth_falsification/`) targeted a misnamed boolean
  proxy, not Paper 0's tuple. See `../semantic_drift_report.md`.
  Those findings are real DESi-behaviour findings about
  composite-EN-label boundaries; they are **not** birth(B)
  falsifications and were not counted here.

## Honest stop

Marginal epistemic gain on additional probes is approximately zero.
Each probe direction has been exercised:

- D — architectural-separation attack.
- R — stylistic-vs-rule attack.
- F — held-out-distribution attack.
- P — silent-overwrite / narrative-repair attack.
- ΔQ — in-distribution-only attack.

Further cycles would repeat one of these five lines against the same
Paper-0 wording. No new falsification path is available without
either:

1. Paper 0 §12.1 wording change (operator's decision, not mine).
2. New empirical evidence: a held-out adversarial distribution
   independent of DESi development (cross-validation against a real
   DES paper7 trajectory dump is the obvious source).

Stop is honest. **birth(B) = 1 holds under Paper 0 §12.1 as written.**

## What this attempt does establish

- The five components are NOT independent in their strength. D, F,
  and ΔQ share a common weakness: the system, its tests, and its
  evaluators were authored by the same agent(s). Cross-validation
  by an unrelated party would strengthen all three at once.

- Paper 0's "lower bound" framing in §12.3 is doing real work. It is
  not rhetorical hedging — it accurately describes what the evidence
  supports.

- A future, stronger birth criterion (call it `birth*`) requiring
  architectural separation, held-out testing, and
  independent-distribution improvement would be falsifiable from the
  current evidence. DESi today is not `birth*` = 1. Paper 0 does not
  claim it is.
