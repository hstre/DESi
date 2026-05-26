# Semantic pre-solver routing — pietrolesci/nli_fever

DESi selects the solver PROMPT MODE per item from epistemic structure (frame consistency + claim authority-grounding), BEFORE the solver runs; it does not answer the item. Identical conditions otherwise: DeepSeek v4 Pro direct, temp 0, one pass, FIXED prompt families, same evaluator. Three policies compared: **A** fixed baseline prompt, **B** benchmark-matched family (chosen by dataset), **C** the semantic router (per-item, no dataset name, no gold label). DESi-core recorded alongside.

N=100 | gold S/R/N = 29/45/26 | matched family = **entailment_direct**

## Policy comparison

| metric | A baseline | B matched (entailment_direct) | C router |
| --- | --- | --- | --- |
| accuracy | 0.57 | 0.58 | 0.55 |
| pred S/R/N | 13/40/47 | 11/44/45 | 11/40/49 |
| SUPPORTS P/R | 0.769/0.345 | 0.545/0.207 | 0.727/0.276 |
| REFUTES P/R | 0.775/0.689 | 0.818/0.800 | 0.775/0.689 |
| NEI P/R | 0.340/0.615 | 0.356/0.615 | 0.327/0.615 |
| overcommitment | 0.385 (10/26) | 0.385 (10/26) | 0.385 (10/26) |
| overabstention | 0.419 (31/74) | 0.392 (29/74) | 0.446 (33/74) |
| parse failures | 0 | 0 | 0 |
| latency | 117.76s | 92.93s | 116.91s |
| est cost | $0.010394 | $0.00949 | $0.010384 |

### Confusion matrices (rows gold, cols pred)

**A baseline**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 10 | 0 | 19 |
| REFUTES | 2 | 31 | 12 |
| NOT_ENOUGH_INFO | 1 | 9 | 16 |

**B matched (entailment_direct)**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 6 | 0 | 23 |
| REFUTES | 3 | 36 | 6 |
| NOT_ENOUGH_INFO | 2 | 8 | 16 |

**C router**

| gold \ pred | SUPPORTS | REFUTES | NOT_ENOUGH_INFO |
| --- | --- | --- | --- |
| SUPPORTS | 8 | 0 | 21 |
| REFUTES | 2 | 31 | 12 |
| NOT_ENOUGH_INFO | 1 | 9 | 16 |

## Router behaviour

Route distribution: baseline 95, evidence_strict 3, entailment_direct 2.

### Per-route accuracy (router-chosen mode vs the same items under baseline)

| routed mode | n | router acc | baseline acc (same items) |
| --- | --- | --- | --- |
| baseline | 95 | 0.558 | 0.558 |
| evidence_strict | 3 | 0.333 | 0.667 |
| entailment_direct | 2 | 0.5 | 1.0 |

- **vs A (baseline)**: router helped 0, hurt 2 (net -2).
- **vs B (benchmark-matched)**: router helped 7, hurt 10 (net -3).

### Semantic features used (and their discrimination)

- Routing signal = `FrameTensionRouter` claim-vs-evidence consistency (CONFIRMED -> entailment-direct; CONFLICT/TENSION -> evidence-strict) + `LogicalAuditor` claim state (authority-rejected -> evidence-strict); else baseline. The `evidence -> claim` formal-inference probe is recorded but NOT routed on: on this dataset it is non-discriminative.
- observed frame_consistency distribution: {'undecidable': 100}.
- observed chain (evidence->claim) state distribution: {'logically_rejected': 98, 'logically_supported': 2} (near-constant -> not usable for routing).

## DESi-core (alongside; core untouched)

- replay stability: 1.0; core identity: True; governance independence: 1.0; critical_branch_preservation: 1.0; mutation rejected: 5/5.
- The router only READS/PROJECTS through frames/logic/frame-tension; it modifies no core module. The router itself is deterministic and replay-stable.

## Honesty / limits

- One deterministic pass per (item, mode); DeepSeek is mildly non-deterministic across runs. Accuracies are the model's; DESi neither solves nor scores. The router selects a policy only; if it does not beat the benchmark-matched family, the limiting factor is which semantic features discriminate this data (reported above), and the core is NOT changed in response.
