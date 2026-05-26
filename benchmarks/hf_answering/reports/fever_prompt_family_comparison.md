# DeepSeek prompt-family comparison — pietrolesci/nli_fever

Task-matched prompt families (prompt-only A/B/C): baseline vs evidence-strict (for over-commitment) vs entailment-direct (for over-abstention). DeepSeek v4 Pro only, direct, temp 0, one deterministic pass; no retries/voting/repair; no Granite/core/evaluator/role-pipeline change. DESi-core recorded alongside.

N=100 | gold S/R/N = 29/45/26

| metric | baseline | evidence-strict | entailment-direct |
| --- | --- | --- | --- |
| accuracy | 0.57 | 0.54 | 0.58 |
| pred S/R/N | 13/39/48 | 7/38/55 | 10/44/46 |
| overcommitment | 0.346 (9/26) | 0.269 (7/26) | 0.385 (10/26) |
| overabstention | 0.419 (31/74) | 0.486 (36/74) | 0.405 (30/74) |
| parse failures | 0 | 0 | 0 |
| elapsed/cost | 122.14s/$0.010354 | 113.55s/$0.011728 | 96.28s/$0.009635 |

### Per-class precision / recall

| class | baseline P/R | evidence_strict P/R | entailment_direct P/R |
| --- | --- | --- | --- |
| SUPPORTS | 0.615/0.276 | 0.429/0.103 | 0.600/0.207 |
| REFUTES | 0.821/0.711 | 0.842/0.711 | 0.818/0.800 |
| NOT_ENOUGH_INFO | 0.354/0.654 | 0.345/0.731 | 0.348/0.615 |

### Confusion (rows gold, cols pred)

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 8 | 0 | 21 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 2 | 7 | 17 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 6 | 0 | 23 |
| REFUTES | 2 | 36 | 7 |
| NOT_ENOUGH_INFO | 2 | 8 | 16 |

### DESi-core (alongside; core untouched)

- replay True; core identity True; governance True; critical_branch_preservation 1.0; mutation 5/5 (identical across all families).

## Honesty / limits

- Prompt-only; one deterministic pass; DeepSeek mild non-determinism; accuracies are the model's. DESi neither solves nor scores.
