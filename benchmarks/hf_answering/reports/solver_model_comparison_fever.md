# Solver-model comparison — pietrolesci/nli_fever

Controlled comparison under IDENTICAL epistemic conditions: same dataset, same FIXED prompt families (baseline / evidence-strict / entailment-direct), same temperature 0, same evaluator and 3-class scoring; the ONLY variable is the solver model. DESi is NOT the solver — it governs alongside and its core metrics are recorded unchanged. No prompt tuning, no benchmark-specific hacks, one deterministic pass per example.

Models: DeepSeek v4 Pro, Claude Haiku 4.5, GPT-4.1-mini, Granite 4.1-8b.

N=100 | gold S/R/N = 29/45/26 | task-matched family = **entailment_direct**

## Accuracy & calibration (rows = model x prompt family)

| model | family | acc | S P/R | R P/R | NEI P/R | overcommit | overabst | parsefail | errors | latency | cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek v4 Pro | baseline | 0.56 | 0.750/0.310 | 0.762/0.711 | 0.326/0.577 | 0.423 (11/26) | 0.419 (31/74) | 0 | 0 | 126.73s | $0.010496 |
| DeepSeek v4 Pro | evidence_strict | 0.52 | 0.429/0.103 | 0.816/0.689 | 0.327/0.692 | 0.308 (8/26) | 0.5 (37/74) | 0 | 0 | 115.48s | $0.011837 |
| DeepSeek v4 Pro | entailment_direct | 0.56 | 0.500/0.172 | 0.814/0.778 | 0.340/0.615 | 0.385 (10/26) | 0.419 (31/74) | 0 | 0 | 97.87s | $0.009611 |
| Claude Haiku 4.5 | baseline | 0.61 | 0.917/0.379 | 0.750/0.800 | 0.350/0.538 | 0.462 (12/26) | 0.351 (26/74) | 0 | 0 | 288.65s | $0.0866 |
| Claude Haiku 4.5 | evidence_strict | 0.552 | 0.500/0.034 | 0.766/0.878 | 0.340/0.615 | 0.385 (10/26) | 0.419 (31/74) | 4 | 0 | 277.42s | $0.13133 |
| Claude Haiku 4.5 | entailment_direct | 0.598 | 0.643/0.310 | 0.771/0.881 | 0.343/0.462 | 0.538 (14/26) | 0.311 (23/74) | 3 | 0 | 291.94s | $0.14301 |
| GPT-4.1-mini | baseline | 0.45 | 0.000/0.000 | 0.784/0.644 | 0.271/0.615 | 0.385 (10/26) | 0.581 (43/74) | 0 | 0 | 202.27s | $0.017234 |
| GPT-4.1-mini | evidence_strict | 0.51 | 0.000/0.000 | 0.842/0.711 | 0.311/0.731 | 0.269 (7/26) | 0.568 (42/74) | 0 | 0 | 192.83s | $0.022903 |
| GPT-4.1-mini | entailment_direct | 0.59 | 0.714/0.345 | 0.846/0.733 | 0.340/0.615 | 0.385 (10/26) | 0.419 (31/74) | 0 | 0 | 371.16s | $0.023113 |
| Granite 4.1-8b | baseline | 0.57 | 0.652/0.517 | 0.744/0.711 | 0.294/0.385 | 0.615 (16/26) | 0.324 (24/74) | 0 | 0 | 89.08s | $0.001763 |
| Granite 4.1-8b | evidence_strict | 0.53 | 0.522/0.414 | 0.763/0.644 | 0.308/0.462 | 0.538 (14/26) | 0.365 (27/74) | 0 | 0 | 106.17s | $0.002373 |
| Granite 4.1-8b | entailment_direct | 0.64 | 0.622/0.793 | 0.767/0.733 | 0.400/0.308 | 0.692 (18/26) | 0.162 (12/74) | 0 | 0 | 89.28s | $0.002239 |

### Predicted class distribution (pred S/R/N per family)

| model | baseline | evidence_strict | entailment_direct |
| --- | --- | --- | --- |
| DeepSeek v4 Pro | 12/42/46 | 7/38/55 | 10/43/47 |
| Claude Haiku 4.5 | 12/48/40 | 2/47/47 | 14/48/35 |
| GPT-4.1-mini | 4/37/59 | 1/38/61 | 14/39/47 |
| Granite 4.1-8b | 23/43/34 | 23/38/39 | 37/43/20 |

## Confusion matrices (rows = gold, cols = pred)

### DeepSeek v4 Pro

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 9 | 0 | 20 |
| REFUTES | 2 | 32 | 11 |
| NOT_ENOUGH_INFO | 1 | 10 | 15 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 31 | 11 |
| NOT_ENOUGH_INFO | 1 | 7 | 18 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 5 | 0 | 24 |
| REFUTES | 3 | 35 | 7 |
| NOT_ENOUGH_INFO | 2 | 8 | 16 |

### Claude Haiku 4.5

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 11 | 1 | 17 |
| REFUTES | 0 | 36 | 9 |
| NOT_ENOUGH_INFO | 1 | 11 | 14 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 1 | 2 | 26 |
| REFUTES | 0 | 36 | 5 |
| NOT_ENOUGH_INFO | 1 | 9 | 16 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 9 | 1 | 19 |
| REFUTES | 1 | 37 | 4 |
| NOT_ENOUGH_INFO | 4 | 10 | 12 |

### GPT-4.1-mini

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 0 | 0 | 29 |
| REFUTES | 2 | 29 | 14 |
| NOT_ENOUGH_INFO | 2 | 8 | 16 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 0 | 0 | 29 |
| REFUTES | 0 | 32 | 13 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 10 | 0 | 19 |
| REFUTES | 0 | 33 | 12 |
| NOT_ENOUGH_INFO | 4 | 6 | 16 |

### Granite 4.1-8b

**baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 15 | 0 | 14 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 5 | 11 | 10 |

**evidence_strict**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 12 | 0 | 17 |
| REFUTES | 6 | 29 | 10 |
| NOT_ENOUGH_INFO | 5 | 9 | 12 |

**entailment_direct**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 23 | 0 | 6 |
| REFUTES | 6 | 33 | 6 |
| NOT_ENOUGH_INFO | 8 | 10 | 8 |

## Read-out (winners among solver candidates DeepSeek / Claude / GPT)

- **Best on the task-matched family (entailment_direct)**: Claude Haiku 4.5 (acc 0.598). All models: DeepSeek v4 Pro 0.56, Claude Haiku 4.5 0.598, GPT-4.1-mini 0.59, Granite 4.1-8b 0.64.
- **Best mean accuracy across the 3 families**: Claude Haiku 4.5 (0.587). All models: DeepSeek v4 Pro 0.547, Claude Haiku 4.5 0.587, GPT-4.1-mini 0.517, Granite 4.1-8b 0.58.
- **Most balanced NEI under the FIXED baseline prompt** (|pred_NEI - gold_NEI|, gold NEI=26): Claude Haiku 4.5 (d14). All models: DeepSeek v4 Pro d20, Claude Haiku 4.5 d14, GPT-4.1-mini d33, Granite 4.1-8b d8.
- *Granite baseline*: matched-family acc 0.64, mean 0.58. Granite is the EXTRACTOR (an 8B model) included only as a direct-solver baseline; where it scores well on the abstention-heavy side it is its over-commitment bias aligning with low-NEI gold, not better reasoning — so it is not treated as a routing target.

## DESi-core (alongside; core untouched, identical across every model & family)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- Intrinsic to DESi's deterministic governance; unchanged when the solver model changes, because DESi neither solves nor scores the verdicts.

## Honesty / limits

- One deterministic pass per example; accuracies are each model's own. DeepSeek (direct api) is mildly non-deterministic across runs; the OpenRouter models at temp 0 are near-deterministic. Granite is the EXTRACTOR by design — shown here only as a direct-solver baseline. Prompt families are FIXED and identical across models; no per-model tuning.
