# FEVER solver-model comparison — CORRECTED mapping

> **Corrected FEVER report.** Previous FEVER results used an INVERTED premise/hypothesis mapping (`claim<-hypothesis, evidence<-premise (INVERTED)`) and are invalid/suspect. Corrected mapping: `claim<-premise, evidence<-hypothesis (CORRECTED)`; labels unchanged.

Identical conditions; only the solver model varies. N=100 | gold S/R/N = 29/45/26 | matched family = **entailment_direct** (DeepSeek arm reused from the corrected residual run).

## Corrected accuracy (model x family)

| model | baseline | evidence-strict | entailment-direct | matched (entailment-direct) |
| --- | --- | --- | --- | --- |
| DeepSeek v4 Pro | 0.8 | 0.8 | 0.8 | 0.8 |
| Claude Haiku 4.5 | 0.77 | 0.76 | 0.76 | 0.76 |
| GPT-4.1-mini | 0.72 | 0.74 | 0.73 | 0.73 |
| Granite 4.1-8b | 0.73 | 0.74 | 0.71 | 0.71 |

## Over-abstention (matched family)

| model | overabstention (matched) | NEI P/R (matched) |
| --- | --- | --- |
| DeepSeek v4 Pro | 0.162 (12/74) | 0.600/0.692 |
| Claude Haiku 4.5 | 0.135 (10/74) | 0.545/0.462 |
| GPT-4.1-mini | 0.176 (13/74) | 0.480/0.462 |
| Granite 4.1-8b | 0.149 (11/74) | 0.476/0.385 |

- **Best on matched family (corrected)**: DeepSeek v4 Pro (0.8).
- **DESi-core (alongside, untouched)**: replay 1.0, core identity True, governance 1.0, critical_branch_preservation 1.0, mutation 5/5.

## Honesty / limits
- One pass; DeepSeek mild non-determinism; corrected mapping only; no prompt/model/evaluator change.
