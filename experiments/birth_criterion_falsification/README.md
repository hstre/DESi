# birth(B) falsification — true target

Branch `experiment/desi-birth-falsification`. Falsification of Paper 0
§12.1's actual definition, after the semantic-drift correction:

```
B = (D, R, F, P, ΔQ)
birth(B) = 1  iff  all five components are present.

D   — Failure Detection of the system's own diagnostic rules.
R   — Revision Proposal: concrete, measurable revisions.
F   — Falsifiability: revisions testable under adversarial conditions.
P   — Preservation of Rejected Paths.
ΔQ  — Measurable Improvement of some accepted revisions.

If any component is absent: birth(B) = 0.
```

(Source: `DESi Paper-0 Birth v1-6.docx` §12, on this branch.)

Paper 0 §12.2 claims DESi satisfies all five. This work is a
disjunctive attack: find ONE component that is *absent* — or so weakly
present that the claim "birth(B) = 1" is unsupported.

## Stance

Adversarial. Paper 0 may be wrong. The cycles below take each
component in turn, propose the strongest absence-hypothesis I can
construct, and report whether evidence in the repo supports forcing
that component to 0.

## Rules (carried over from earlier loops)

- DESi source under `src/desi/` is NOT modified.
- Each cycle: hypothesis → evidence → verdict.
- Failed hypotheses preserved.
- No prior metrics rewritten.
- Stop when marginal epistemic gain approaches zero.

## Distinction from the prior (mislabelled) attempt

The directory `experiments/composite_en_label_falsification/`
(formerly `experiments/birth_falsification/`) probed the composite
EN classifier label, NOT birth(B). See
`../semantic_drift_report.md` for the post-mortem of that drift.
This directory probes the actual §12.1 criterion.

## Cycle log

| # | Component | Hypothesis | Verdict | Forces birth(B)=0? |
|--:|---|---|---|:---:|
| 1 | D  | "Failure detector" is the same LLM as the diagnosed system | Weakly satisfied — pytest + suite metrics meet literal wording | No |
| 2 | R  | Some "accepted" revisions are stylistic, not concrete-measurable | Satisfied — stylistic cycles still concrete/measurable per §12.1 | No |
| 3 | F  | Revisions tested only on suites authored with knowledge of DESi's failure modes | Satisfied — §12.1 requires testability + rejection-tolerance, both met | No |
| 4 | P  | Silent overwrites / narrative-repair / history rewrites occurred | Satisfied with documented frictions (comment-trimming, drift rename) — neither hides behaviour | No |
| 5 | ΔQ | ΔQ is in-distribution only; held-out improvement unestablished | Satisfied in-distribution; held-out unestablished per Paper 0 §11.10 itself | No |

**Disjunctive conclusion: birth(B) = 1 holds under Paper 0 §12.1 as
written.** None of the five components can be forced to 0 from what
the repo contains. See `synthesis.md` for the detailed argument and
the fragility note (D, F, ΔQ would each flip under stricter wording).
