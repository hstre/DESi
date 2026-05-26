# Role-separation comparison — vitaminc

Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is not the solver. Roles: granite_structured (extraction) / deepseek_semantic (verdict).

## Comparative accuracy & behavior

| config | solver | acc | answered | parse-fail | pred dist | cost | elapsed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| granite_only | `ibm-granite/granite-4.1-8b` | 0.560 | 100 | 0 | SUP:56/REF:42/NOT:2 | $0.00168 | 102.07s |
| deepseek_only | `deepseek-chat (direct)` | 0.740 | 100 | 0 | SUP:46/REF:34/NOT:20 | $0.01068 | 150.08s |
| role | `deepseek-chat (direct)` + extractor | 0.620 | 100 | 0 | SUP:50/REF:44/NOT:6 | $0.01437 | 285.08s |

Gold distribution: SUPPORTS=31, REFUTES=28, NOT_ENOUGH_INFO=41.

## Confusion matrices (rows=gold, cols=pred)

**granite_only**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 1 | 0 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 24 | 16 | 1 |

**deepseek_only**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 1 | 1 |
| REFUTES | 2 | 26 | 0 |
| NOT_ENOUGH_INFO | 15 | 7 | 19 |

**role**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 2 | 0 |
| REFUTES | 1 | 27 | 0 |
| NOT_ENOUGH_INFO | 20 | 15 | 6 |

## DESi-core metrics (per config; recorded alongside)

| config | replay | core id | crit_pres | hard_prune | mut rej |
| --- | --- | --- | --- | --- | --- |
| granite_only | 1.0 | 1.0 | 1.0 | 0 | 5/5 |
| deepseek_only | 1.0 | 1.0 | 1.0 | 0 | 5/5 |
| role | 1.0 | 1.0 | 1.0 | 0 | 5/5 |

## Honesty / limits

- One deterministic pass per config; no retries, no repair, no voting. Accuracy is the MODEL pipeline's; DESi neither reasons nor scores.
- Granite = extractor only (config role); DeepSeek = solver. DESi-core recorded alongside is intrinsic and unchanged by any config.
