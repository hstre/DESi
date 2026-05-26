# Semantic-unfolding routing — pietrolesci/nli_fever

Unfolding does the opposite of similarity-folding: it uses deterministic signals to catch *superficially similar but epistemically dangerous differences* (directional / operator / relation / negation divergence) and PROTECTS against a false 'direct-entailment' fold. Policies: **A** baseline, **B** benchmark-matched, **C** DESi semantic-router, **D** micro-router, **E** unfolding-aware. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. No LLM in the detector; DESi core untouched, recorded alongside.

N=100 | gold S/R/N = 29/45/26 | matched family = **entailment_direct**

## Policy comparison

| metric | A baseline | B matched (entailment_direct) | C DESi-router | D micro-router | E unfolding |
| --- | --- | --- | --- | --- | --- |
| accuracy | 0.57 | 0.56 | 0.55 | 0.53 | 0.54 |
| pred S/R/N | 14/42/44 | 9/43/48 | 12/42/46 | 7/39/54 | 7/38/55 |
| SUPPORTS P/R | 0.643/0.310 | 0.556/0.172 | 0.583/0.241 | 0.429/0.103 | 0.429/0.103 |
| REFUTES P/R | 0.786/0.733 | 0.814/0.778 | 0.786/0.733 | 0.821/0.711 | 0.842/0.711 |
| NEI P/R | 0.341/0.577 | 0.333/0.615 | 0.326/0.577 | 0.333/0.692 | 0.345/0.731 |
| overcommitment | 0.423 (11/26) | 0.385 (10/26) | 0.423 (11/26) | 0.308 (8/26) | 0.269 (7/26) |
| overabstention | 0.392 (29/74) | 0.432 (32/74) | 0.419 (31/74) | 0.486 (36/74) | 0.486 (36/74) |
| parse failures | 0 | 0 | 0 | 0 | 0 |
| latency | 114.57s | 90.2s | 113.79s | 104.34s | 103.0s |
| est cost | $0.010424 | $0.009543 | $0.010433 | $0.011707 | $0.01166 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 9 | 0 | 20 |
| REFUTES | 3 | 33 | 9 |
| NOT_ENOUGH_INFO | 2 | 9 | 15 |

**B matched (entailment_direct)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 5 | 0 | 24 |
| REFUTES | 2 | 35 | 8 |
| NOT_ENOUGH_INFO | 2 | 8 | 16 |

**C DESi-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 7 | 0 | 22 |
| REFUTES | 3 | 33 | 9 |
| NOT_ENOUGH_INFO | 2 | 9 | 15 |

**D micro-router**

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

## Unfolding behaviour

Fold candidates (applicable): 10/100; unfold triggers: 10.

Category distribution: fold_safe 90, contradiction_masking 0, directional_divergence 0, operator_divergence 0, semantic_near_epistemic_far 8, partial_support_masking 2.

E route distribution: {'evidence_strict': 99, 'baseline': 1}.

- **Cases prevented from false folding**: 1 (unfold fired, an entailment-direct fold would have been WRONG, and the protected route is right).
- **Cases over-protected**: 0 (unfold fired, but the entailment fold would have been right and protection lost it).

### Per-category accuracy (E's routed prediction within each category)

| unfold category | n | E accuracy |
| --- | --- | --- |
| fold_safe | 90 | 0.544 |
| contradiction_masking | 0 | None |
| directional_divergence | 0 | None |
| operator_divergence | 0 | None |
| semantic_near_epistemic_far | 8 | 0.5 |
| partial_support_masking | 2 | 0.5 |

- **vs C (DESi-router)**: helped 8, hurt 9 (net -1).
- **vs D (micro-router)**: helped 1, hurt 0 (net +1).
- **vs A (baseline)**: net -3; **vs B (matched)**: net -2.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The unfolding detector is deterministic string/token arithmetic over the micro-router's features; it does not import or modify the DESi core or ontology.

## Honesty / limits

- One deterministic pass per (item, variant); DeepSeek mildly non-deterministic. Accuracies are the model's; the detector only re-routes a policy and never emits a verdict. NOT a truthfulness claim; DESi did not solve NLI. If unfolding does not beat the matched family, the limiting factor is reported (which divergence signals fire / are absent), and the core is NOT changed.
