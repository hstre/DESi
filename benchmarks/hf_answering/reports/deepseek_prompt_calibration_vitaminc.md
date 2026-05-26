# DeepSeek prompt-only calibration — tals/vitaminc

Prompt-only A/B: the only change is the evidence-style solver prompt (baseline vs calibrated). DeepSeek v4 Pro only, direct, temp 0, one deterministic pass, no retries/voting/repair. No Granite, no DESi-core change. DESi-core recorded alongside.

N=100 | gold S/R/N = 31/28/41

| metric | baseline | calibrated |
| --- | --- | --- |
| accuracy | 0.72 | 0.79 |
| pred S/R/N | 45/37/18 | 28/28/44 |
| overcommitment rate (gold-NEI committed) | 0.585 (24/41) | 0.195 (8/41) |
| overabstention rate (gold-S/R -> NEI) | 0.017 (1/59) | 0.186 (11/59) |
| parse failures | 0 | 0 |
| elapsed / cost | 127.1s / $0.010572 | 142.12s / $0.015351 |

### Per-class precision / recall

| class | baseline P | baseline R | calibrated P | calibrated R |
| --- | --- | --- | --- | --- |
| SUPPORTS | 0.644 | 0.935 | 0.857 | 0.774 |
| REFUTES | 0.703 | 0.929 | 0.786 | 0.786 |
| NOT_ENOUGH_INFO | 0.944 | 0.415 | 0.750 | 0.805 |

### Confusion (rows gold, cols pred)

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 1 | 1 |
| REFUTES | 2 | 26 | 0 |
| NOT_ENOUGH_INFO | 14 | 10 | 17 |

**calibrated**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 24 | 1 | 6 |
| REFUTES | 1 | 22 | 5 |
| NOT_ENOUGH_INFO | 3 | 5 | 33 |

### DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.

## Honesty / limits

- Prompt-only change; one deterministic pass; accuracies are the model's. DeepSeek is mildly non-deterministic across runs. DESi neither solves nor scores.
