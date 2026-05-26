# Residual semantic escalation — pietrolesci/nli_fever

Algorithm-first: the deterministic micro-router + unfolding protection resolve clear cases; only the ambiguous residue escalates to a lightweight deterministic semantic scorer (synonym-group + character-trigram vectors with directional containment / asymmetry -- NO learned neural embeddings are available offline here, so the vectors are deterministic local lexical-semantic vectors; this is a documented constraint). Policies: **A** baseline, **B** benchmark-matched, **C** DESi semantic-router, **D** micro-router, **E** unfolding-aware, **F** residual escalation. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. No LLM in any router; DESi core untouched, recorded alongside.

N=100 | gold S/R/N = 29/45/26 | matched family = **entailment_direct**

## Policy comparison

| metric | A baseline | B matched (entailment_direct) | C DESi-router | D micro | E unfolding | F residual |
| --- | --- | --- | --- | --- | --- | --- |
| accuracy | 0.54 | 0.58 | 0.53 | 0.53 | 0.54 | 0.54 |
| pred S/R/N | 13/41/46 | 11/42/47 | 12/41/47 | 7/39/54 | 7/38/55 | 7/38/55 |
| SUPPORTS P/R | 0.615/0.276 | 0.545/0.207 | 0.583/0.241 | 0.429/0.103 | 0.429/0.103 | 0.429/0.103 |
| REFUTES P/R | 0.780/0.711 | 0.833/0.778 | 0.780/0.711 | 0.821/0.711 | 0.842/0.711 | 0.842/0.711 |
| NEI P/R | 0.304/0.538 | 0.362/0.654 | 0.298/0.538 | 0.333/0.692 | 0.345/0.731 | 0.345/0.731 |
| overcommitment | 0.462 (12/26) | 0.346 (9/26) | 0.462 (12/26) | 0.308 (8/26) | 0.269 (7/26) | 0.269 (7/26) |
| overabstention | 0.432 (32/74) | 0.405 (30/74) | 0.446 (33/74) | 0.486 (36/74) | 0.486 (36/74) | 0.486 (36/74) |
| parse failures | 0 | 0 | 0 | 0 | 0 | 0 |
| latency | 110.63s | 88.0s | 109.45s | 108.46s | 107.52s | 107.52s |
| est cost | $0.010465 | $0.009569 | $0.010475 | $0.011875 | $0.011782 | $0.011782 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 8 | 0 | 21 |
| REFUTES | 2 | 32 | 11 |
| NOT_ENOUGH_INFO | 3 | 9 | 14 |

**B matched (entailment_direct)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 6 | 0 | 23 |
| REFUTES | 3 | 35 | 7 |
| NOT_ENOUGH_INFO | 2 | 7 | 17 |

**C DESi-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 7 | 0 | 22 |
| REFUTES | 2 | 32 | 11 |
| NOT_ENOUGH_INFO | 3 | 9 | 14 |

**D micro**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 1 | 7 | 18 |

**E unfolding**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

**F residual**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 32 | 10 |
| NOT_ENOUGH_INFO | 1 | 6 | 19 |

## Residual escalation behaviour

Escalated (residue only): 10/100; escalation accuracy (F on the escalated subset): 0.5; escalation net vs E on that subset: +0 (helped 0, hurt 0).

Outcome distribution: fold_safe_confirmed 0, directional_entailment_confirmed 0, semantic_divergence_confirmed 9, partial_support_confirmed 1, unresolved_high_risk 0.

F route distribution: {'evidence_strict': 99, 'baseline': 1}.

- **False folds prevented**: 4; **over-protected**: 8.

### Per-outcome accuracy (escalated cases)

| residual outcome | n | F accuracy |
| --- | --- | --- |
| fold_safe_confirmed | 0 | None |
| directional_entailment_confirmed | 0 | None |
| semantic_divergence_confirmed | 9 | 0.444 |
| partial_support_confirmed | 1 | 1.0 |
| unresolved_high_risk | 0 | None |

- **vs E (unfolding)**: net +0 (helped 0, hurt 0). **vs D (micro)**: net +1. **vs C (DESi)**: net +1.
- **vs A (baseline)**: net +0. **vs B (matched)**: net -4.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The residual scorer is deterministic local vector arithmetic; it does not import or modify the DESi core or ontology, and runs only on the escalated residue.

## Honesty / limits

- One deterministic pass per (item, variant); DeepSeek mildly non-deterministic. The residual 'semantic vectors' are deterministic local lexical-semantic vectors (no learned embeddings available offline). Accuracies are the model's; routers only pick a policy. NOT a truthfulness claim; DESi did not solve NLI. Limits reported, core unchanged.
