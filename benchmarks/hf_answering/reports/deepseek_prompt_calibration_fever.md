# DeepSeek prompt-only calibration — pietrolesci/nli_fever

Prompt-only A/B: the only change is the evidence-style solver prompt (baseline vs calibrated). DeepSeek v4 Pro only, direct, temp 0, one deterministic pass, no retries/voting/repair. No Granite, no DESi-core change. DESi-core recorded alongside.

N=100 | gold S/R/N = 29/45/26

| metric | baseline | calibrated |
| --- | --- | --- |
| accuracy | 0.55 | 0.53 |
| pred S/R/N | 13/39/48 | 7/37/56 |
| overcommitment rate (gold-NEI committed) | 0.385 (10/26) | 0.269 (7/26) |
| overabstention rate (gold-S/R -> NEI) | 0.432 (32/74) | 0.5 (37/74) |
| parse failures | 0 | 0 |
| elapsed / cost | 127.31s / $0.01028 | 116.27s / $0.011832 |

### Per-class precision / recall

| class | baseline P | baseline R | calibrated P | calibrated R |
| --- | --- | --- | --- | --- |
| SUPPORTS | 0.538 | 0.241 | 0.429 | 0.103 |
| REFUTES | 0.821 | 0.711 | 0.838 | 0.689 |
| NOT_ENOUGH_INFO | 0.333 | 0.615 | 0.339 | 0.731 |

### Confusion (rows gold, cols pred)

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 7 | 0 | 22 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 3 | 7 | 16 |

**calibrated**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 31 | 11 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

### DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.

## Honesty / limits

- Prompt-only change; one deterministic pass; accuracies are the model's. DeepSeek is mildly non-deterministic across runs. DESi neither solves nor scores.
