# FEVER semantic-router study — CORRECTED mapping

> **Corrected FEVER report.** Previous FEVER results used an INVERTED premise/hypothesis mapping (`claim<-hypothesis, evidence<-premise (INVERTED)`) and are invalid/suspect. Corrected mapping: `claim<-premise, evidence<-hypothesis (CORRECTED)`; labels unchanged.

Policies: A baseline, B benchmark-matched, C semantic-router-selected.

## Corrected accuracy

| policy | accuracy | overcommit | overabst |
| --- | --- | --- | --- |
| A baseline | 0.81 | 0.346 | 0.122 |
| B matched | 0.8 | 0.308 | 0.162 |
| C router | 0.81 | 0.346 | 0.122 |

- Route distribution: baseline 100 / evidence-strict 0 / entailment-direct 0.
- Router net vs baseline +0, vs matched +1.

## Old (inverted) vs corrected accuracy

| policy | old | corrected |
| --- | --- | --- |
| baseline | 0.57 | 0.81 |
| matched | 0.58 | 0.8 |
| router | 0.55 | 0.81 |

- **DESi-core (alongside, untouched)**: replay 1.0, core identity True, governance 1.0, critical_branch_preservation 1.0, mutation 5/5.

## Honesty / limits
- Corrected mapping only; semantic router unchanged; DeepSeek mild non-determinism.
