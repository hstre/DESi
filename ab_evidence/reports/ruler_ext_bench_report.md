# RULER-Extended A/B Results (32k / 64k / 131k) — Run 2 (Replication)

Total items: 180

## Per length × task × model × variant

| length | task | n | DS A | DS B | ΔDS | GR A | GR B | ΔGR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 32768 | niah_multikey_2 | 20 | 0.65 | 1.0 | +0.350 | 0.55 | 0.95 | +0.400 |
| 32768 | niah_single_1 | 20 | 0.75 | 0.85 | +0.100 | 0.85 | 0.95 | +0.100 |
| 32768 | niah_single_3 | 20 | 0.0 | 0.45 | +0.450 | 0.7 | 1.0 | +0.300 |
| 65536 | niah_multikey_2 | 20 | 0.85 | 1.0 | +0.150 | 0.3 | 1.0 | +0.700 |
| 65536 | niah_single_1 | 20 | 0.75 | 0.85 | +0.100 | 0.85 | 1.0 | +0.150 |
| 65536 | niah_single_3 | 20 | 0.0 | 0.45 | +0.450 | 0.3 | 0.95 | +0.650 |
| 131072 | niah_multikey_2 | 20 | 0.8 | 0.95 | +0.150 | 0.0 | 0.85 | +0.850 |
| 131072 | niah_single_1 | 20 | 0.75 | 0.9 | +0.150 | 0.0 | 0.8 | +0.800 |
| 131072 | niah_single_3 | 20 | 0.0 | 0.6 | +0.600 | 0.0 | 0.85 | +0.850 |

## Per length (mean across tasks)

| length | n | DS A | DS B | ΔDS | GR A | GR B | ΔGR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 32768 | 60 | 0.467 | 0.767 | +0.300 | 0.700 | 0.967 | +0.267 |
| 65536 | 60 | 0.533 | 0.767 | +0.233 | 0.483 | 0.983 | +0.500 |
| 131072 | 60 | 0.517 | 0.817 | +0.300 | 0.000 | 0.833 | +0.833 |

## Error rate per (model, variant, length)

| length | model | variant | error_rate | n_errors |
| --- | --- | --- | --- | --- |
| 32768 | deepseek-v4-pro | A | 0.00% | 0/60 |
| 32768 | deepseek-v4-pro | B | 0.00% | 0/60 |
| 32768 | granite-4.1-8b | A | 0.00% | 0/60 |
| 32768 | granite-4.1-8b | B | 0.00% | 0/60 |
| 65536 | deepseek-v4-pro | A | 0.00% | 0/60 |
| 65536 | deepseek-v4-pro | B | 0.00% | 0/60 |
| 65536 | granite-4.1-8b | A | 0.00% | 0/60 |
| 65536 | granite-4.1-8b | B | 0.00% | 0/60 |
| 131072 | deepseek-v4-pro | A | 0.00% | 0/60 |
| 131072 | deepseek-v4-pro | B | 0.00% | 0/60 |
| 131072 | granite-4.1-8b | A | **100.00%** | 60/60 |
| 131072 | granite-4.1-8b | B | 0.00% | 0/60 |

## Tokens & cost

| model | variant | mean_in | sum_in | sum_out | cost_$ |
| --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | A | 76239 | 13723100 | 20181 | $5.918 |
| deepseek-v4-pro | B | 139 | 24935 | 17517 | $0.026 |
| granite-4.1-8b | A | 51138 | 6136615 | 5053 | $0.307 |
| granite-4.1-8b | B | 155 | 27843 | 2230 | $0.002 |

Total cost: **$6.25**
