# Small-LLM unfolding gate — tals/vitaminc

A small cheap LLM (`ibm-granite/granite-4.1-8b`) decides ONLY UNFOLD / DO_NOT_UNFOLD / UNCERTAIN on the ambiguous residue (never a verdict); the decision selects the solver prompt mode and DeepSeek produces the verdict. To isolate the gate, the DeepSeek predictions for all three prompt variants are REUSED from the residual-escalation run, so A/B/C are identical to that study and the only new variable is the gate decision on escalated items. One gate call per escalated item, no retries/voting/CoT, temp 0. DESi-core recorded alongside; core untouched.

Policies: **A** matched-prompt ceiling, **B** deterministic unfolding, **C** residual lexical-semantic escalation, **D** small-LLM unfolding gate.

N=100 | gold S/R/N = 31/28/41

## Policy comparison

| metric | A matched (evidence_strict) | B unfolding | C residual | D LLM-gate |
| --- | --- | --- | --- | --- |
| accuracy | 0.768 | 0.73 | 0.72 | 0.72 |
| pred S/R/N | 29/27/43 | 44/27/29 | 44/28/28 | 47/26/27 |
| SUPPORTS P/R | 0.828/0.774 | 0.636/0.903 | 0.636/0.903 | 0.617/0.935 |
| REFUTES P/R | 0.815/0.786 | 0.852/0.821 | 0.821/0.821 | 0.846/0.786 |
| NEI P/R | 0.698/0.750 | 0.759/0.537 | 0.750/0.512 | 0.778/0.512 |
| overcommitment | 0.244 (10/41) | 0.463 (19/41) | 0.488 (20/41) | 0.488 (20/41) |
| overabstention | 0.22 (13/59) | 0.119 (7/59) | 0.119 (7/59) | 0.102 (6/59) |
| parse failures (solver) | 1 | 0 | 0 | 0 |

### Confusion matrices (rows gold, cols pred)

**A matched (evidence_strict)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 24 | 0 | 7 |
| REFUTES | 0 | 22 | 6 |
| NOT_ENOUGH_INFO | 5 | 5 | 30 |

**B unfolding**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 0 | 3 |
| REFUTES | 1 | 23 | 4 |
| NOT_ENOUGH_INFO | 15 | 4 | 22 |

**C residual**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 1 | 2 |
| REFUTES | 0 | 23 | 5 |
| NOT_ENOUGH_INFO | 16 | 4 | 21 |

**D LLM-gate**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 0 | 2 |
| REFUTES | 2 | 22 | 4 |
| NOT_ENOUGH_INFO | 16 | 4 | 21 |

## Gate behaviour

Escalated (gate calls): 45/100; decision distribution: {'UNFOLD': 18, 'DO_NOT_UNFOLD': 27}; parse failures: 0; network errors: 0.

Gate cost: $0.000831 (13879+1366 tok); gate latency: 17.76s (DeepSeek solver cost reused, not re-billed).

- **vs B (deterministic unfolding)**: helped 1, hurt 2 (net -1).
- **vs C (residual lexical)**: helped 1, hurt 1 (net +0).
- **vs A (matched ceiling)**: net -4.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The gate is a peripheral routing aid: it selects a prompt mode and never emits a verdict; it does not import or modify the DESi core.

## Honesty / limits

- DeepSeek predictions reused from the residual run (A/B/C identical to it); the gate adds one Granite call per escalated item. Gate emits only UNFOLD/DO_NOT_UNFOLD/UNCERTAIN. Accuracies are DeepSeek's; the gate only routes. NOT a truthfulness claim; DESi did not solve NLI. Key in-process only; outputs secret-scanned.
