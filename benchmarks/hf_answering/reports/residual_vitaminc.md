# Residual semantic escalation — tals/vitaminc

Algorithm-first: the deterministic micro-router + unfolding protection resolve clear cases; only the ambiguous residue escalates to a lightweight deterministic semantic scorer (synonym-group + character-trigram vectors with directional containment / asymmetry -- NO learned neural embeddings are available offline here, so the vectors are deterministic local lexical-semantic vectors; this is a documented constraint). Policies: **A** baseline, **B** benchmark-matched, **C** DESi semantic-router, **D** micro-router, **E** unfolding-aware, **F** residual escalation. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. No LLM in any router; DESi core untouched, recorded alongside.

N=100 | gold S/R/N = 31/28/41 | matched family = **evidence_strict**

## Policy comparison

| metric | A baseline | B matched (evidence_strict) | C DESi-router | D micro | E unfolding | F residual |
| --- | --- | --- | --- | --- | --- | --- |
| accuracy | 0.72 | 0.768 | 0.72 | 0.72 | 0.73 | 0.72 |
| pred S/R/N | 47/33/20 | 29/27/43 | 46/33/21 | 46/26/28 | 44/27/29 | 44/28/28 |
| SUPPORTS P/R | 0.638/0.968 | 0.828/0.774 | 0.630/0.935 | 0.609/0.903 | 0.636/0.903 | 0.636/0.903 |
| REFUTES P/R | 0.727/0.857 | 0.815/0.786 | 0.727/0.857 | 0.846/0.786 | 0.852/0.821 | 0.821/0.821 |
| NEI P/R | 0.900/0.439 | 0.698/0.750 | 0.905/0.463 | 0.786/0.537 | 0.759/0.537 | 0.750/0.512 |
| overcommitment | 0.561 (23/41) | 0.244 (10/41) | 0.537 (22/41) | 0.463 (19/41) | 0.463 (19/41) | 0.488 (20/41) |
| overabstention | 0.034 (2/59) | 0.22 (13/59) | 0.034 (2/59) | 0.102 (6/59) | 0.119 (7/59) | 0.119 (7/59) |
| parse failures | 0 | 1 | 0 | 0 | 0 | 0 |
| latency | 109.75s | 124.78s | 110.66s | 106.55s | 107.86s | 107.98s |
| est cost | $0.010662 | $0.015451 | $0.011639 | $0.011497 | $0.01172 | $0.011721 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 1 | 0 |
| REFUTES | 2 | 24 | 2 |
| NOT_ENOUGH_INFO | 15 | 8 | 18 |

**B matched (evidence_strict)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 24 | 0 | 7 |
| REFUTES | 0 | 22 | 6 |
| NOT_ENOUGH_INFO | 5 | 5 | 30 |

**C DESi-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 2 | 0 |
| REFUTES | 2 | 24 | 2 |
| NOT_ENOUGH_INFO | 15 | 7 | 19 |

**D micro**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 1 | 2 |
| REFUTES | 2 | 22 | 4 |
| NOT_ENOUGH_INFO | 16 | 3 | 22 |

**E unfolding**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 0 | 3 |
| REFUTES | 1 | 23 | 4 |
| NOT_ENOUGH_INFO | 15 | 4 | 22 |

**F residual**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 1 | 2 |
| REFUTES | 0 | 23 | 5 |
| NOT_ENOUGH_INFO | 16 | 4 | 21 |

## Residual escalation behaviour

Escalated (residue only): 45/100; escalation accuracy (F on the escalated subset): 0.689; escalation net vs E on that subset: -1 (helped 0, hurt 1).

Outcome distribution: fold_safe_confirmed 0, directional_entailment_confirmed 10, semantic_divergence_confirmed 1, partial_support_confirmed 34, unresolved_high_risk 0.

F route distribution: {'baseline': 47, 'evidence_strict': 43, 'entailment_direct': 10}.

- **False folds prevented**: 8; **over-protected**: 10.

### Per-outcome accuracy (escalated cases)

| residual outcome | n | F accuracy |
| --- | --- | --- |
| fold_safe_confirmed | 0 | None |
| directional_entailment_confirmed | 10 | 0.7 |
| semantic_divergence_confirmed | 1 | 1.0 |
| partial_support_confirmed | 34 | 0.676 |
| unresolved_high_risk | 0 | None |

- **vs E (unfolding)**: net -1 (helped 0, hurt 1). **vs D (micro)**: net +0. **vs C (DESi)**: net +0.
- **vs A (baseline)**: net +0. **vs B (matched)**: net -4.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The residual scorer is deterministic local vector arithmetic; it does not import or modify the DESi core or ontology, and runs only on the escalated residue.

## Honesty / limits

- One deterministic pass per (item, variant); DeepSeek mildly non-deterministic. The residual 'semantic vectors' are deterministic local lexical-semantic vectors (no learned embeddings available offline). Accuracies are the model's; routers only pick a policy. NOT a truthfulness claim; DESi did not solve NLI. Limits reported, core unchanged.
