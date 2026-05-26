# Algorithmic micro-semantic routing — tals/vitaminc

A deterministic, LLM-free micro-layer computes lexical-semantic features (content coverage, entity overlap, negation/antonym/numeric contradiction cues) and picks the solver PROMPT MODE per item, before the solver runs. Everything algorithmic is decided here; the LLM handles the residue. Identical conditions otherwise (DeepSeek v4 Pro, temp 0, one pass, FIXED families, same evaluator). Policies: **A** baseline, **B** benchmark-matched, **C** the existing DESi semantic-flow router, **D** the new micro-router. DESi-core recorded alongside; this micro-layer does NOT touch the DESi core.

N=100 | gold S/R/N = 31/28/41 | matched family = **evidence_strict**

## Policy comparison

| metric | A baseline | B matched (evidence_strict) | C DESi-router | D micro-router |
| --- | --- | --- | --- | --- |
| accuracy | 0.75 | 0.79 | 0.71 | 0.73 |
| pred S/R/N | 47/32/21 | 31/28/41 | 47/33/20 | 47/26/27 |
| SUPPORTS P/R | 0.638/0.968 | 0.806/0.806 | 0.617/0.935 | 0.596/0.903 |
| REFUTES P/R | 0.781/0.893 | 0.821/0.821 | 0.727/0.857 | 0.885/0.821 |
| NEI P/R | 0.952/0.488 | 0.756/0.756 | 0.900/0.439 | 0.815/0.537 |
| overcommitment | 0.512 (21/41) | 0.244 (10/41) | 0.561 (23/41) | 0.463 (19/41) |
| overabstention | 0.017 (1/59) | 0.169 (10/59) | 0.034 (2/59) | 0.085 (5/59) |
| parse failures | 0 | 0 | 0 | 0 |
| latency | 113.7s | 121.31s | 112.72s | 109.06s |
| est cost | $0.010804 | $0.014799 | $0.0115 | $0.011415 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 30 | 1 | 0 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 15 | 6 | 20 |

**B matched (evidence_strict)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 25 | 0 | 6 |
| REFUTES | 1 | 23 | 4 |
| NOT_ENOUGH_INFO | 5 | 5 | 31 |

**C DESi-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 29 | 2 | 0 |
| REFUTES | 2 | 24 | 2 |
| NOT_ENOUGH_INFO | 16 | 7 | 18 |

**D micro-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 1 | 2 |
| REFUTES | 2 | 23 | 3 |
| NOT_ENOUGH_INFO | 17 | 2 | 22 |

## Micro-router behaviour

Mode distribution: direct_entailment_likely 13, contradiction_likely 47, missing_linkage_risk 11, partial_support_risk 29, high_nei_risk 0, ambiguous 0.

Policy distribution: {'baseline': 47, 'evidence_strict': 40, 'entailment_direct': 13}.

### Per-route accuracy (micro-chosen mode vs the same items under baseline)

| micro mode | policy | n | micro acc | baseline acc (same items) |
| --- | --- | --- | --- | --- |
| direct_entailment_likely | entailment_direct | 13 | 0.615 | 0.769 |
| contradiction_likely | baseline | 47 | 0.723 | 0.723 |
| missing_linkage_risk | evidence_strict | 11 | 0.727 | 0.727 |
| partial_support_risk | evidence_strict | 29 | 0.793 | 0.793 |
| high_nei_risk | evidence_strict | 0 | None | None |
| ambiguous | baseline | 0 | None | None |

- **vs A (baseline)**: helped 5, hurt 7 (net -2).
- **vs B (benchmark-matched)**: helped 6, hurt 12 (net -6).
- **vs C (DESi semantic-router)**: helped 6, hurt 4 (net +2).

### Features used (deterministic, no LLM)

- normalized content tokens + synonym groups -> content coverage (claim covered by evidence); capitalized proper-noun overlap -> entity overlap; negation / antonym / numeric-mismatch -> contradiction cue; quantifier / modality / temporal marker counts. Decision precedence: contradiction -> direct-entailment (high coverage + entity overlap) -> missing-linkage (claim entities absent) -> high-NEI (near-zero coverage) -> partial-support (mid coverage) -> ambiguous.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The micro-router is a self-contained benchmark adapter (pure string/token arithmetic). It does not import or modify the DESi semantic core or ontology.

## Honesty / limits

- One deterministic pass per (item, mode); DeepSeek mildly non-deterministic. Accuracies are the model's; the router only picks a policy and never produces a verdict. This is NOT a truthfulness claim and DESi did not solve NLI. If the micro-router does not beat the benchmark-matched family, the limiting factor is feature coverage (reported above), and the core is NOT changed in response.
