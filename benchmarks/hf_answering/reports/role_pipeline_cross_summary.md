# Role-pipeline cross-summary — restored core

Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is not the solver. Granite = extractor; DeepSeek = semantic solver.

## Accuracy by config

| benchmark | granite_only | deepseek_only | role (G->DS) |
| --- | --- | --- | --- |
| boolq | 0.860 | 0.830 | 0.880 |
| vitaminc | 0.560 | 0.740 | 0.620 |

## Cross questions

- **boolq: role vs baselines** — granite_only 0.860, deepseek_only 0.830, role 0.880 -> role pipeline best (0.880).
- **vitaminc: role vs baselines** — granite_only 0.560, deepseek_only 0.740, role 0.620 -> deepseek_only best; role=0.620.
- **vitaminc: abstention (NOT_ENOUGH_INFO)** gold=41, deepseek_only pred=20, role pred=6 -> role does not improve abstention calibration.
- **Does Granite improve semantic stability for DeepSeek?** see per-benchmark role vs deepseek_only above (accuracy + abstention calibration).
- **Does the architecture reduce over-support / over-abstain?** compare role pred distribution to deepseek_only against gold (per benchmark above).
- **Does DESi-core remain invariant?** YES — across all 6 config runs: replay stable, core byte-identical, critical_branch_preservation 1.0, hard_pruning 0, mutation fully rejected.

## Honesty / limits

- 100 examples/config, one deterministic pass, no tuning/retries/voting. Accuracies are the model pipelines'; DESi neither solves nor scores. Whether the original Granite/DeepSeek split is justified is read directly off the role-vs-baseline rows — reported as measured, not asserted.
