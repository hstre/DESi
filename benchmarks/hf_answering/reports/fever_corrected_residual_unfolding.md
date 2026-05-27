# FEVER residual / unfolding study — CORRECTED mapping

> **Corrected FEVER report.** Previous FEVER results used an INVERTED premise/hypothesis mapping (`claim<-hypothesis, evidence<-premise (INVERTED)`) and are invalid/suspect. Corrected mapping: `claim<-premise, evidence<-hypothesis (CORRECTED)`; labels unchanged.

Policies: matched, unfolding, residual (plus baseline/micro for context).

## Corrected accuracy

| policy | accuracy | overcommit | overabst |
| --- | --- | --- | --- |
| B matched | 0.8 | 0.308 | 0.162 |
| E unfolding | 0.81 | 0.269 | 0.162 |
| F residual | 0.82 | 0.269 | 0.149 |
| A baseline | 0.8 | 0.346 | 0.135 |
| D micro | 0.82 | 0.269 | 0.149 |

- Escalated (residue): 65/100; residual net vs unfolding +1.

## Old vs corrected accuracy

| policy | old | corrected |
| --- | --- | --- |
| B matched | 0.58 | 0.8 |
| E unfolding | 0.54 | 0.81 |
| F residual | 0.54 | 0.82 |
| A baseline | 0.54 | 0.8 |
| D micro | 0.53 | 0.82 |

- **DESi-core (alongside, untouched)**: replay 1.0, core identity True, governance 1.0, critical_branch_preservation 1.0, mutation 5/5.

## Honesty / limits
- Corrected mapping only; routers unchanged.
