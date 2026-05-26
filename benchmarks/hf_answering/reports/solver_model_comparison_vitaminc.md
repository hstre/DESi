# Solver-model comparison — tals/vitaminc

Controlled comparison under IDENTICAL epistemic conditions: same dataset, same FIXED prompt families (baseline / evidence-strict / entailment-direct), same temperature 0, same evaluator and 3-class scoring; the ONLY variable is the solver model. DESi is NOT the solver — it governs alongside and its core metrics are recorded unchanged. No prompt tuning, no benchmark-specific hacks, one deterministic pass per example.

Models: DeepSeek v4 Pro, Claude Haiku 4.5, GPT-4.1-mini, Granite 4.1-8b.

N=100 | gold S/R/N = 31/28/41 | task-matched family = **evidence_strict**

## Accuracy & calibration (rows = model x prompt family)

| model | family | acc | S P/R | R P/R | NEI P/R | overcommit | overabst | parsefail | errors | latency | cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek v4 Pro | baseline | 0.75 | 0.652/0.968 | 0.758/0.893 | 0.952/0.488 | 0.512 (21/41) | 0.017 (1/59) | 0 | 0 | 122.02s | $0.011172 |
| DeepSeek v4 Pro | evidence_strict | 0.78 | 0.828/0.774 | 0.815/0.786 | 0.727/0.780 | 0.22 (9/41) | 0.203 (12/59) | 0 | 0 | 133.77s | $0.015303 |
| DeepSeek v4 Pro | entailment_direct | 0.72 | 0.583/0.903 | 0.774/0.857 | 0.952/0.488 | 0.512 (21/41) | 0.017 (1/59) | 0 | 0 | 95.93s | $0.009114 |
| Claude Haiku 4.5 | baseline | 0.59 | 0.604/0.935 | 0.545/0.857 | 0.750/0.146 | 0.854 (35/41) | 0.034 (2/59) | 0 | 0 | 236.52s | $0.089546 |
| Claude Haiku 4.5 | evidence_strict | 0.765 | 0.867/0.839 | 0.649/0.857 | 0.806/0.641 | 0.341 (14/41) | 0.102 (6/59) | 2 | 0 | 354.86s | $0.153741 |
| Claude Haiku 4.5 | entailment_direct | 0.67 | 0.659/0.935 | 0.610/0.893 | 0.867/0.317 | 0.683 (28/41) | 0.034 (2/59) | 0 | 0 | 435.01s | $0.148886 |
| GPT-4.1-mini | baseline | 0.68 | 0.651/0.903 | 0.658/0.893 | 0.789/0.366 | 0.634 (26/41) | 0.068 (4/59) | 0 | 0 | 183.1s | $0.016426 |
| GPT-4.1-mini | evidence_strict | 0.81 | 0.757/0.903 | 0.885/0.821 | 0.811/0.732 | 0.268 (11/41) | 0.119 (7/59) | 0 | 0 | 251.48s | $0.02633 |
| GPT-4.1-mini | entailment_direct | 0.73 | 0.630/0.935 | 0.806/0.893 | 0.826/0.463 | 0.537 (22/41) | 0.068 (4/59) | 0 | 0 | 222.12s | $0.024913 |
| Granite 4.1-8b | baseline | 0.57 | 0.536/0.968 | 0.610/0.893 | 0.667/0.049 | 0.951 (39/41) | 0.017 (1/59) | 0 | 0 | 102.46s | $0.001692 |
| Granite 4.1-8b | evidence_strict | 0.61 | 0.492/0.968 | 0.806/0.893 | 0.750/0.146 | 0.854 (35/41) | 0.034 (2/59) | 0 | 0 | 106.88s | $0.002257 |
| Granite 4.1-8b | entailment_direct | 0.58 | 0.492/0.968 | 0.735/0.893 | 0.600/0.073 | 0.927 (38/41) | 0.034 (2/59) | 0 | 0 | 98.28s | $0.002209 |

### Predicted class distribution (pred S/R/N per family)

| model | baseline | evidence_strict | entailment_direct |
| --- | --- | --- | --- |
| DeepSeek v4 Pro | 46/33/21 | 29/27/44 | 48/31/21 |
| Claude Haiku 4.5 | 48/44/8 | 30/37/31 | 44/41/15 |
| GPT-4.1-mini | 43/38/19 | 37/26/37 | 46/31/23 |
| Granite 4.1-8b | 56/41/3 | 61/31/8 | 61/34/5 |

## Confusion matrices (rows = gold, cols = pred)

### DeepSeek v4 Pro

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 1 | 0 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 14 | 7 | 20 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 24 | 0 | 7 |
| REFUTES | 1 | 22 | 5 |
| NOT_ENOUGH_INFO | 4 | 5 | 32 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 3 | 0 |
| REFUTES | 3 | 24 | 1 |
| NOT_ENOUGH_INFO | 17 | 4 | 20 |

### Claude Haiku 4.5

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 2 | 0 |
| REFUTES | 2 | 24 | 2 |
| NOT_ENOUGH_INFO | 17 | 18 | 6 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 26 | 3 | 2 |
| REFUTES | 0 | 24 | 4 |
| NOT_ENOUGH_INFO | 4 | 10 | 25 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 2 | 0 |
| REFUTES | 1 | 25 | 2 |
| NOT_ENOUGH_INFO | 14 | 14 | 13 |

### GPT-4.1-mini

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 1 | 2 |
| REFUTES | 1 | 25 | 2 |
| NOT_ENOUGH_INFO | 14 | 12 | 15 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 0 | 3 |
| REFUTES | 1 | 23 | 4 |
| NOT_ENOUGH_INFO | 8 | 3 | 30 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 0 | 2 |
| REFUTES | 1 | 25 | 2 |
| NOT_ENOUGH_INFO | 16 | 6 | 19 |

### Granite 4.1-8b

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 1 | 0 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 24 | 15 | 2 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 0 | 1 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 29 | 6 | 6 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 0 | 1 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 29 | 9 | 3 |

## Read-out (winners among solver candidates DeepSeek / Claude / GPT)

- **Best on the task-matched family (evidence_strict)**: GPT-4.1-mini (acc 0.81). All models: DeepSeek v4 Pro 0.78, Claude Haiku 4.5 0.765, GPT-4.1-mini 0.81, Granite 4.1-8b 0.61.
- **Best mean accuracy across the 3 families**: DeepSeek v4 Pro (0.75). All models: DeepSeek v4 Pro 0.75, Claude Haiku 4.5 0.675, GPT-4.1-mini 0.74, Granite 4.1-8b 0.587.
- **Most balanced NEI under the FIXED baseline prompt** (|pred_NEI - gold_NEI|, gold NEI=41): DeepSeek v4 Pro (d20). All models: DeepSeek v4 Pro d20, Claude Haiku 4.5 d33, GPT-4.1-mini d22, Granite 4.1-8b d38.
- *Granite baseline*: matched-family acc 0.61, mean 0.587. Granite is the EXTRACTOR (an 8B model) included only as a direct-solver baseline; where it scores well on the abstention-heavy side it is its over-commitment bias aligning with low-NEI gold, not better reasoning — so it is not treated as a routing target.

## DESi-core (alongside; core untouched, identical across every model & family)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- Intrinsic to DESi's deterministic governance; unchanged when the solver model changes, because DESi neither solves nor scores the verdicts.

## Honesty / limits

- One deterministic pass per example; accuracies are each model's own. DeepSeek (direct api) is mildly non-deterministic across runs; the OpenRouter models at temp 0 are near-deterministic. Granite is the EXTRACTOR by design — shown here only as a direct-solver baseline. Prompt families are FIXED and identical across models; no per-model tuning.
