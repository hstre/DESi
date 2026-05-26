# Role-separation comparison — boolq

Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is not the solver. Roles: granite_structured (extraction) / deepseek_semantic (verdict).

## Comparative accuracy & behavior

| config | solver | acc | answered | parse-fail | pred dist | cost | elapsed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| granite_only | `ibm-granite/granite-4.1-8b` | 0.860 | 100 | 0 | YES:68/NO:32 | $0.00170 | 76.7s |
| deepseek_only | `deepseek-chat (direct)` | 0.830 | 100 | 0 | YES:57/NO:43 | $0.01055 | 155.31s |
| role | `deepseek-chat (direct)` + extractor | 0.880 | 100 | 0 | YES:66/NO:34 | $0.01198 | 271.17s |

Gold distribution: YES=70, NO=30.

## Confusion matrices (rows=gold, cols=pred)

**granite_only**

| gold \ pred | YES | NO |
| --- | --- | --- |
| YES | 62 | 8 |
| NO | 6 | 24 |

**deepseek_only**

| gold \ pred | YES | NO |
| --- | --- | --- |
| YES | 55 | 15 |
| NO | 2 | 28 |

**role**

| gold \ pred | YES | NO |
| --- | --- | --- |
| YES | 62 | 8 |
| NO | 4 | 26 |

## DESi-core metrics (per config; recorded alongside)

| config | replay | core id | crit_pres | hard_prune | mut rej |
| --- | --- | --- | --- | --- | --- |
| granite_only | 1.0 | 1.0 | 1.0 | 0 | 5/5 |
| deepseek_only | 1.0 | 1.0 | 1.0 | 0 | 5/5 |
| role | 1.0 | 1.0 | 1.0 | 0 | 5/5 |

## Honesty / limits

- One deterministic pass per config; no retries, no repair, no voting. Accuracy is the MODEL pipeline's; DESi neither reasons nor scores.
- Granite = extractor only (config role); DeepSeek = solver. DESi-core recorded alongside is intrinsic and unchanged by any config.
