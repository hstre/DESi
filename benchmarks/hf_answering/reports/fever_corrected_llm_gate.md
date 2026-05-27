# FEVER small-LLM unfold-gate study — CORRECTED mapping

> **Corrected FEVER report.** Previous FEVER results used an INVERTED premise/hypothesis mapping (`claim<-hypothesis, evidence<-premise (INVERTED)`) and are invalid/suspect. Corrected mapping: `claim<-premise, evidence<-hypothesis (CORRECTED)`; labels unchanged.

Gate model: `ibm-granite/granite-4.1-8b` (decides only UNFOLD/DO_NOT_UNFOLD/UNCERTAIN).

## Corrected accuracy

| policy | accuracy | overabst |
| --- | --- | --- |
| A matched | 0.8 | 0.162 |
| B unfolding | 0.81 | 0.162 |
| C residual | 0.82 | 0.149 |
| D LLM-gate | 0.82 | 0.149 |

- Escalated: 65; decisions {'UNFOLD': 44, 'DO_NOT_UNFOLD': 21}; parse failures 0; gate net vs unfolding +1; cost $0.00123.

## Old vs corrected accuracy

| policy | old | corrected |
| --- | --- | --- |
| A matched | 0.58 | 0.8 |
| B unfolding | 0.54 | 0.81 |
| C residual | 0.54 | 0.82 |
| D LLM-gate | 0.54 | 0.82 |

- **DESi-core (alongside, untouched)**: replay 1.0, core identity True, governance 1.0, critical_branch_preservation 1.0, mutation 5/5.

## Honesty / limits
- Corrected mapping only; gate unchanged; DeepSeek preds reused from the corrected residual run.
