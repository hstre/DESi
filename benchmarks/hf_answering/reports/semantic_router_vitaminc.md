# Semantic pre-solver routing — tals/vitaminc

DESi selects the solver PROMPT MODE per item from epistemic structure (frame consistency + claim authority-grounding), BEFORE the solver runs; it does not answer the item. Identical conditions otherwise: DeepSeek v4 Pro direct, temp 0, one pass, FIXED prompt families, same evaluator. Three policies compared: **A** fixed baseline prompt, **B** benchmark-matched family (chosen by dataset), **C** the semantic router (per-item, no dataset name, no gold label). DESi-core recorded alongside.

N=100 | gold S/R/N = 31/28/41 | matched family = **evidence_strict**

## Policy comparison

| metric | A baseline | B matched (evidence_strict) | C router |
| --- | --- | --- | --- |
| accuracy | 0.71 | 0.76 | 0.68 |
| pred S/R/N | 46/35/19 | 30/28/42 | 47/36/17 |
| SUPPORTS P/R | 0.609/0.903 | 0.800/0.774 | 0.596/0.903 |
| REFUTES P/R | 0.743/0.929 | 0.786/0.786 | 0.694/0.893 |
| NEI P/R | 0.895/0.415 | 0.714/0.732 | 0.882/0.366 |
| overcommitment | 0.585 (24/41) | 0.268 (11/41) | 0.634 (26/41) |
| overabstention | 0.034 (2/59) | 0.203 (12/59) | 0.034 (2/59) |
| parse failures | 0 | 0 | 0 |
| latency | 117.32s | 129.83s | 115.11s |
| est cost | $0.010843 | $0.014988 | $0.011424 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 1 | 2 |
| REFUTES | 2 | 26 | 0 |
| NOT_ENOUGH_INFO | 16 | 8 | 17 |

**B matched (evidence_strict)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 24 | 0 | 7 |
| REFUTES | 1 | 22 | 5 |
| NOT_ENOUGH_INFO | 5 | 6 | 30 |

**C router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 28 | 2 | 1 |
| REFUTES | 2 | 25 | 1 |
| NOT_ENOUGH_INFO | 17 | 9 | 15 |

## Router behaviour

Route distribution: baseline 64, evidence_strict 12, entailment_direct 24.

### Per-route accuracy (router-chosen mode vs the same items under baseline)

| routed mode | n | router acc | baseline acc (same items) |
| --- | --- | --- | --- |
| baseline | 64 | 0.766 | 0.766 |
| evidence_strict | 12 | 0.5 | 0.667 |
| entailment_direct | 24 | 0.542 | 0.583 |

- **vs A (baseline)**: router helped 3, hurt 6 (net -3).
- **vs B (benchmark-matched)**: router helped 10, hurt 18 (net -8).

### Semantic features used (and their discrimination)

- Routing signal = `FrameTensionRouter` claim-vs-evidence consistency (CONFIRMED -> entailment-direct; CONFLICT/TENSION -> evidence-strict) + `LogicalAuditor` claim state (authority-rejected -> evidence-strict); else baseline. The `evidence -> claim` formal-inference probe is recorded but NOT routed on: on this dataset it is non-discriminative.
- observed frame_consistency distribution: {'undecidable': 64, 'confirmed': 36}.
- observed chain (evidence->claim) state distribution: {'logically_rejected': 100} (near-constant -> not usable for routing).

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The router only READS/PROJECTS through frames/logic/frame-tension; it modifies no core module. The router itself is deterministic and replay-stable.

## Honesty / limits

- One deterministic pass per (item, mode); DeepSeek is mildly non-deterministic across runs. Accuracies are the model's; DESi neither solves nor scores. The router selects a policy only; if it does not beat the benchmark-matched family, the limiting factor is which semantic features discriminate this data (reported above), and the core is NOT changed in response.
