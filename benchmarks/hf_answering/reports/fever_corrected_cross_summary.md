# FEVER corrected cross-summary

> **Corrected FEVER report.** Previous FEVER results used an INVERTED premise/hypothesis mapping (`claim<-hypothesis, evidence<-premise (INVERTED)`) and are invalid/suspect. Corrected mapping: `claim<-premise, evidence<-hypothesis (CORRECTED)`; labels unchanged.

## Final answers

- **Was FEVER mapping inverted?** YES -- `pietrolesci/nli_fever` stores the short claim in `premise` and the long evidence in `hypothesis`; the prior loader mapped claim<-hypothesis / evidence<-premise, feeding a long claim against a short evidence and forcing NOT_ENOUGH_INFO.
- **Which old FEVER conclusions are invalidated?** All prior FEVER numbers and the claims built on them: the "~0.58 FEVER ceiling", "DeepSeek over-abstains on FEVER", "entailment-direct is the FEVER-matched family", and every FEVER arm of the solver-model / semantic-router / micro / unfolding / residual / gate studies. They were measured on inverted inputs.
- **Corrected FEVER prompt-family results**: baseline 0.8 (was 0.57), evidence_strict 0.8 (was 0.54), entailment_direct 0.8 (was 0.58); best = baseline.
- **Does DeepSeek still over-abstain on FEVER?** Corrected over-abstention: baseline 0.135, entailment-direct 0.162 (compare to old baseline 0.419). Read the corrected NEI recall to judge whether the over-abstention was a mapping artifact rather than a model trait.
- **Does prompt-family calibration still matter?** Best corrected family is baseline (acc 0.8); compare the spread across families above.
- **Does semantic routing still underperform on FEVER?** corrected router 0.81 vs baseline 0.81 vs matched 0.8.
- **DESi-core (alongside, untouched)**: replay 1.0, core identity True, governance 1.0, critical_branch_preservation 1.0, mutation 5/5.
- **Did DESi-core remain invariant?** YES on every corrected run (replay stable, core byte-identical, governance independent, mutation rejected).

## Honesty / limits

- N=100; one deterministic pass; DeepSeek mild non-determinism; ONLY the dataset mapping was corrected (no prompt/model/evaluator/router/core change). VitaminC untouched (its mapping was already correct).
