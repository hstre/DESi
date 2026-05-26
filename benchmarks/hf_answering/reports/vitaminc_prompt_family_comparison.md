# DeepSeek prompt-family comparison — tals/vitaminc

Task-matched prompt families (prompt-only A/B/C): baseline vs evidence-strict (for over-commitment) vs entailment-direct (for over-abstention). DeepSeek v4 Pro only, direct, temp 0, one deterministic pass; no retries/voting/repair; no Granite/core/evaluator/role-pipeline change. DESi-core recorded alongside.

N=100 | gold S/R/N = 31/28/41

| metric | baseline | evidence-strict | entailment-direct |
| --- | --- | --- | --- |
| accuracy | 0.73 | 0.78 | 0.73 |
| pred S/R/N | 46/33/21 | 28/28/44 | 48/30/22 |
| overcommitment | 0.537 (22/41) | 0.22 (9/41) | 0.488 (20/41) |
| overabstention | 0.034 (2/59) | 0.203 (12/59) | 0.017 (1/59) |
| parse failures | 0 | 0 | 0 |
| elapsed/cost | 127.03s/$0.010722 | 139.96s/$0.015248 | 93.83s/$0.009144 |

### Per-class precision / recall

| class | baseline P/R | evidence_strict P/R | entailment_direct P/R |
| --- | --- | --- | --- |
| SUPPORTS | 0.630/0.935 | 0.821/0.742 | 0.583/0.903 |
| REFUTES | 0.758/0.893 | 0.821/0.821 | 0.800/0.857 |
| NOT_ENOUGH_INFO | 0.905/0.463 | 0.727/0.780 | 0.955/0.512 |

### Confusion (rows gold, cols pred)

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 1 | 1 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 15 | 7 | 19 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 23 | 0 | 8 |
| REFUTES | 1 | 23 | 4 |
| NOT_ENOUGH_INFO | 4 | 5 | 32 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 3 | 0 |
| REFUTES | 3 | 24 | 1 |
| NOT_ENOUGH_INFO | 17 | 3 | 21 |

### DESi-core (alongside; core untouched)

- replay True; core identity True; governance True; critical_branch_preservation 1.0; mutation 5/5 (identical across all families).

## Honesty / limits

- Prompt-only; one deterministic pass; DeepSeek mild non-determinism; accuracies are the model's. DESi neither solves nor scores.
