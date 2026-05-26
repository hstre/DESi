# Semantic-unfolding routing — tals/vitaminc

Unfolding does the opposite of similarity-folding: it uses deterministic signals to catch *superficially similar but epistemically dangerous differences* (directional / operator / relation / negation divergence) and PROTECTS against a false 'direct-entailment' fold. Policies: **A** baseline, **B** benchmark-matched, **C** DESi semantic-router, **D** micro-router, **E** unfolding-aware. DeepSeek v4 Pro, temp 0, FIXED families, same evaluator. No LLM in the detector; DESi core untouched, recorded alongside.

N=100 | gold S/R/N = 31/28/41 | matched family = **evidence_strict**

## Policy comparison

| metric | A baseline | B matched (evidence_strict) | C DESi-router | D micro-router | E unfolding |
| --- | --- | --- | --- | --- | --- |
| accuracy | 0.73 | 0.77 | 0.7 | 0.71 | 0.72 |
| pred S/R/N | 46/36/18 | 30/27/43 | 47/35/18 | 47/28/25 | 45/29/26 |
| SUPPORTS P/R | 0.652/0.968 | 0.800/0.774 | 0.617/0.935 | 0.596/0.903 | 0.622/0.903 |
| REFUTES P/R | 0.722/0.929 | 0.815/0.786 | 0.714/0.893 | 0.821/0.821 | 0.828/0.857 |
| NEI P/R | 0.944/0.415 | 0.721/0.756 | 0.889/0.390 | 0.800/0.488 | 0.769/0.488 |
| overcommitment | 0.585 (24/41) | 0.244 (10/41) | 0.61 (25/41) | 0.512 (21/41) | 0.512 (21/41) |
| overabstention | 0.017 (1/59) | 0.203 (12/59) | 0.034 (2/59) | 0.085 (5/59) | 0.102 (6/59) |
| parse failures | 0 | 0 | 0 | 0 | 0 |
| latency | 111.89s | 126.83s | 113.19s | 109.12s | 110.9s |
| est cost | $0.010729 | $0.014977 | $0.011574 | $0.011286 | $0.011574 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 1 | 0 |
| REFUTES | 1 | 26 | 1 |
| NOT_ENOUGH_INFO | 15 | 9 | 17 |

**B matched (evidence_strict)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 24 | 0 | 7 |
| REFUTES | 1 | 22 | 5 |
| NOT_ENOUGH_INFO | 5 | 5 | 31 |

**C DESi-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 2 | 0 |
| REFUTES | 1 | 25 | 2 |
| NOT_ENOUGH_INFO | 17 | 8 | 16 |

**D micro-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 1 | 2 |
| REFUTES | 2 | 23 | 3 |
| NOT_ENOUGH_INFO | 17 | 4 | 20 |

**E unfolding**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 0 | 3 |
| REFUTES | 1 | 24 | 3 |
| NOT_ENOUGH_INFO | 16 | 5 | 20 |

## Unfolding behaviour

Fold candidates (applicable): 85/100; unfold triggers: 78.

Category distribution: fold_safe 22, contradiction_masking 38, directional_divergence 2, operator_divergence 0, semantic_near_epistemic_far 3, partial_support_masking 35.

E route distribution: {'baseline': 47, 'evidence_strict': 46, 'entailment_direct': 7}.

- **Cases prevented from false folding**: 10 (unfold fired, an entailment-direct fold would have been WRONG, and the protected route is right).
- **Cases over-protected**: 10 (unfold fired, but the entailment fold would have been right and protection lost it).

### Per-category accuracy (E's routed prediction within each category)

| unfold category | n | E accuracy |
| --- | --- | --- |
| fold_safe | 22 | 0.773 |
| contradiction_masking | 38 | 0.711 |
| directional_divergence | 2 | 1.0 |
| operator_divergence | 0 | None |
| semantic_near_epistemic_far | 3 | 0.667 |
| partial_support_masking | 35 | 0.686 |

- **vs C (DESi-router)**: helped 7, hurt 5 (net +2).
- **vs D (micro-router)**: helped 2, hurt 1 (net +1).
- **vs A (baseline)**: net -1; **vs B (matched)**: net -5.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The unfolding detector is deterministic string/token arithmetic over the micro-router's features; it does not import or modify the DESi core or ontology.

## Honesty / limits

- One deterministic pass per (item, variant); DeepSeek mildly non-deterministic. Accuracies are the model's; the detector only re-routes a policy and never emits a verdict. NOT a truthfulness claim; DESi did not solve NLI. If unfolding does not beat the matched family, the limiting factor is reported (which divergence signals fire / are absent), and the core is NOT changed.
