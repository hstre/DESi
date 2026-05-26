# Dissent ('wild brother') comparison — vitaminc

Hypothesis: Granite compresses uncertainty too early; an adversarial / dissent-oriented parallel path (Nemotron-3-Super as epistemic challenger) should better preserve NOT_ENOUGH_INFO. Pipeline: Granite extract -> Nemotron dissent -> DeepSeek solve. DESi = governance alongside (uncertainty loss / branch pruning / replayability); DESi is not the solver. Benchmarks run on DESi; they do not redefine DESi.

N=10 per config (same examples). Reduced N because Nemotron-3-Super (free, reasoning) runs ~23s/example.

Gold distribution: SUPPORTS=3, REFUTES=2, NOT_ENOUGH_INFO=5 (NEI base rate 5/10).

## Calibration comparison

| config | acc | pred NEI | abstention rate | NEI gap (pred-gold) | branch preservation |
| --- | --- | --- | --- | --- | --- |
| granite_only | 0.600 | 1 | 0.1 | -4 | - |
| deepseek_only | 1.000 | 5 | 0.5 | +0 | - |
| role | 0.700 | 3 | 0.3 | -2 | - |
| dissent | 0.500 | 10 | 1.0 | +5 | 1.0 |

## Dissent / disagreement propagation (dissent config)

- challenger flagged NOT_ENOUGH_INFO plausible: **8** of 10
- dissent preserved (flagged -> final NEI): **8**
- dissent hard-pruned (flagged but overridden by solver): **0**
- branch preservation rate: **1.0**

## Does the dissent layer improve epistemic calibration?

- **NEI calibration** (smaller |pred-gold| is better): granite_only 4, deepseek_only 0, role 2, dissent 5 -> best calibrated: **deepseek_only**.
- **Accuracy**: granite_only 0.600, deepseek_only 1.000, role 0.700, dissent 0.500 -> highest: **deepseek_only**.
- **dissent vs DeepSeek-only**: acc 0.500 vs 1.000; NEI gap 5 vs 0 -> dissent does NOT improve calibration over DeepSeek-only.

## DESi governance (alongside; core untouched)

- uncertainty improperly lost (challenger NEI overridden): 0
- challenger branches hard-pruned: 0
- decision structure replayable: True
- DESi-core invariant across all configs: True

## Honesty / limits

- Small N (Nemotron free-tier latency ~23s/example); one deterministic pass, no retries/repair/voting. Calibration read as measured, not asserted. Accuracies are the model pipelines'; DESi neither solves nor scores.
