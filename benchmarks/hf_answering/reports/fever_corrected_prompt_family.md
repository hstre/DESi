# FEVER prompt-family comparison — CORRECTED mapping

> **Corrected FEVER report.** Previous FEVER results used an INVERTED premise/hypothesis mapping (`claim<-hypothesis, evidence<-premise (INVERTED)`) and are invalid/suspect. Corrected mapping: `claim<-premise, evidence<-hypothesis (CORRECTED)`; labels unchanged.

DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. N=100 | gold S/R/N = 29/45/26 | matched family = **entailment_direct**.

## Corrected results

| metric | baseline | evidence-strict | entailment-direct |
| --- | --- | --- | --- |
| accuracy | 0.8 | 0.8 | 0.8 |
| pred S/R/N | 31/42/27 | 29/39/32 | 31/39/30 |
| SUPPORTS P/R | 0.871/0.931 | 0.897/0.897 | 0.903/0.966 |
| REFUTES P/R | 0.857/0.800 | 0.897/0.778 | 0.872/0.756 |
| NEI P/R | 0.630/0.654 | 0.594/0.731 | 0.600/0.692 |
| overcommitment | 0.346 (9/26) | 0.269 (7/26) | 0.308 (8/26) |
| overabstention | 0.135 (10/74) | 0.176 (13/74) | 0.162 (12/74) |

## Old (inverted) vs corrected — accuracy & over-abstention

| family | old acc | corrected acc | old overabst | corrected overabst |
| --- | --- | --- | --- | --- |
| baseline | 0.57 | 0.8 | 0.419 | 0.135 |
| evidence_strict | 0.54 | 0.8 | 0.486 | 0.176 |
| entailment_direct | 0.58 | 0.8 | 0.405 | 0.162 |

- **Best corrected family**: baseline (acc 0.8).
- **DESi-core (alongside, untouched)**: replay 1.0, core identity True, governance 1.0, critical_branch_preservation 1.0, mutation 5/5.

## Honesty / limits

- DeepSeek mildly non-deterministic; one pass; corrected mapping only. Accuracies are the model's; DESi did not solve NLI.
