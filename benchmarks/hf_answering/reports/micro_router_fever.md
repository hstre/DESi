# Algorithmic micro-semantic routing — pietrolesci/nli_fever

A deterministic, LLM-free micro-layer computes lexical-semantic features (content coverage, entity overlap, negation/antonym/numeric contradiction cues) and picks the solver PROMPT MODE per item, before the solver runs. Everything algorithmic is decided here; the LLM handles the residue. Identical conditions otherwise (DeepSeek v4 Pro, temp 0, one pass, FIXED families, same evaluator). Policies: **A** baseline, **B** benchmark-matched, **C** the existing DESi semantic-flow router, **D** the new micro-router. DESi-core recorded alongside; this micro-layer does NOT touch the DESi core.

N=100 | gold S/R/N = 29/45/26 | matched family = **entailment_direct**

## Policy comparison

| metric | A baseline | B matched (entailment_direct) | C DESi-router | D micro-router |
| --- | --- | --- | --- | --- |
| accuracy | 0.51 | 0.59 | 0.49 | 0.52 |
| pred S/R/N | 14/38/48 | 11/44/45 | 12/38/50 | 7/38/55 |
| SUPPORTS P/R | 0.571/0.276 | 0.636/0.241 | 0.500/0.207 | 0.429/0.103 |
| REFUTES P/R | 0.763/0.644 | 0.818/0.800 | 0.763/0.644 | 0.816/0.689 |
| NEI P/R | 0.292/0.538 | 0.356/0.615 | 0.280/0.538 | 0.327/0.692 |
| overcommitment | 0.462 (12/26) | 0.385 (10/26) | 0.462 (12/26) | 0.308 (8/26) |
| overabstention | 0.459 (34/74) | 0.392 (29/74) | 0.486 (36/74) | 0.5 (37/74) |
| parse failures | 0 | 0 | 0 | 0 |
| latency | 114.0s | 90.17s | 113.14s | 104.5s |
| est cost | $0.010373 | $0.009619 | $0.01038 | $0.0117 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 8 | 0 | 21 |
| REFUTES | 3 | 29 | 13 |
| NOT_ENOUGH_INFO | 3 | 9 | 14 |

**B matched (entailment_direct)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 7 | 0 | 22 |
| REFUTES | 2 | 36 | 7 |
| NOT_ENOUGH_INFO | 2 | 8 | 16 |

**C DESi-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 6 | 0 | 23 |
| REFUTES | 3 | 29 | 13 |
| NOT_ENOUGH_INFO | 3 | 9 | 14 |

**D micro-router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 3 | 0 | 26 |
| REFUTES | 3 | 31 | 11 |
| NOT_ENOUGH_INFO | 1 | 7 | 18 |

## Micro-router behaviour

Mode distribution: direct_entailment_likely 0, contradiction_likely 1, missing_linkage_risk 80, partial_support_risk 3, high_nei_risk 10, ambiguous 6.

Policy distribution: {'evidence_strict': 93, 'baseline': 7}.

### Per-route accuracy (micro-chosen mode vs the same items under baseline)

| micro mode | policy | n | micro acc | baseline acc (same items) |
| --- | --- | --- | --- | --- |
| direct_entailment_likely | entailment_direct | 0 | None | None |
| contradiction_likely | baseline | 1 | 0.0 | 0.0 |
| missing_linkage_risk | evidence_strict | 80 | 0.575 | 0.562 |
| partial_support_risk | evidence_strict | 3 | 0.667 | 0.667 |
| high_nei_risk | evidence_strict | 10 | 0.2 | 0.2 |
| ambiguous | baseline | 6 | 0.333 | 0.333 |

- **vs A (baseline)**: helped 9, hurt 8 (net +1).
- **vs B (benchmark-matched)**: helped 3, hurt 10 (net -7).
- **vs C (DESi semantic-router)**: helped 9, hurt 6 (net +3).

### Features used (deterministic, no LLM)

- normalized content tokens + synonym groups -> content coverage (claim covered by evidence); capitalized proper-noun overlap -> entity overlap; negation / antonym / numeric-mismatch -> contradiction cue; quantifier / modality / temporal marker counts. Decision precedence: contradiction -> direct-entailment (high coverage + entity overlap) -> missing-linkage (claim entities absent) -> high-NEI (near-zero coverage) -> partial-support (mid coverage) -> ambiguous.

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The micro-router is a self-contained benchmark adapter (pure string/token arithmetic). It does not import or modify the DESi semantic core or ontology.

## Honesty / limits

- One deterministic pass per (item, mode); DeepSeek mildly non-deterministic. Accuracies are the model's; the router only picks a policy and never produces a verdict. This is NOT a truthfulness claim and DESi did not solve NLI. If the micro-router does not beat the benchmark-matched family, the limiting factor is feature coverage (reported above), and the core is NOT changed in response.
