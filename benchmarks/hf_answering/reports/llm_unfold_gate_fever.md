# Small-LLM unfolding gate — pietrolesci/nli_fever

A small cheap LLM (`ibm-granite/granite-4.1-8b`) decides ONLY UNFOLD / DO_NOT_UNFOLD / UNCERTAIN on the ambiguous residue (never a verdict); the decision selects the solver prompt mode and DeepSeek produces the verdict. To isolate the gate, the DeepSeek predictions for all three prompt variants are REUSED from the residual-escalation run, so A/B/C are identical to that study and the only new variable is the gate decision on escalated items. One gate call per escalated item, no retries/voting/CoT, temp 0. DESi-core recorded alongside; core untouched.

Policies: **A** matched-prompt ceiling, **B** deterministic unfolding, **C** residual lexical-semantic escalation, **D** small-LLM unfolding gate.

N=100 | gold S/R/N = 29/45/26

## Policy comparison

| metric | A matched (entailment_direct) | B unfolding | C residual | D LLM-gate |
| --- | --- | --- | --- | --- |
| accuracy | 0.58 | 0.54 | 0.54 | 0.54 |
| pred S/R/N | 11/42/47 | 7/38/55 | 7/38/55 | 7/38/55 |
| SUPPORTS P/R | 0.545/0.207 | 0.429/0.103 | 0.429/0.103 | 0.429/0.103 |
| REFUTES P/R | 0.833/0.778 | 0.842/0.711 | 0.842/0.711 | 0.842/0.711 |
| NEI P/R | 0.362/0.654 | 0.345/0.731 | 0.345/0.731 | 0.345/0.731 |
| overcommitment | 0.346 (9/26) | 0.269 (7/26) | 0.269 (7/26) | 0.269 (7/26) |
| overabstention | 0.405 (30/74) | 0.486 (36/74) | 0.486 (36/74) | 0.486 (36/74) |
| parse failures (solver) | 0 | 0 | 0 | 0 |

### Confusion matrices (rows gold, cols pred)

**A matched (entailment_direct)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 6 | 0 | 23 |
| REFUTES | 3 | 35 | 7 |
| NOT_ENOUGH_INFO | 2 | 7 | 17 |

**B unfolding**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

**C residual**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

**D LLM-gate**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

## Gate behaviour

Escalated (gate calls): 10/100; decision distribution: {'UNFOLD': 7, 'DO_NOT_UNFOLD': 3}; parse failures: 0; network errors: 0.

Gate cost: $0.000172 (2903+272 tok); gate latency: 4.05s (DeepSeek solver cost reused, not re-billed).

- **vs B (deterministic unfolding)**: helped 0, hurt 0 (net +0).
- **vs C (residual lexical)**: helped 0, hurt 0 (net +0).
- **vs A (matched ceiling)**: net -4.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The gate is a peripheral routing aid: it selects a prompt mode and never emits a verdict; it does not import or modify the DESi core.

## Honesty / limits

- DeepSeek predictions reused from the residual run (A/B/C identical to it); the gate adds one Granite call per escalated item. Gate emits only UNFOLD/DO_NOT_UNFOLD/UNCERTAIN. Accuracies are DeepSeek's; the gate only routes. NOT a truthfulness claim; DESi did not solve NLI. Key in-process only; outputs secret-scanned.
