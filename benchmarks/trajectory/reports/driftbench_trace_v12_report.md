# DriftBench TrajectoryTrace v1.2 — semantic branch folding

Folds the brief's plausible_directions into epistemic branch CLUSTERS (deterministic: stopword/filler reduction + method-synonym canonicalisation + normalized-token Jaccard union-find), measuring branch diversity over clusters, not raw lexical directions. v1/v1.1 unchanged. No LLM/embeddings/Neo4j; core read-only.

## Pre-analysis (why this is hard)

- DriftBench's plausible_directions are mostly DISTINCT by design: only ~1.8% of direction pairs are lexically near (Jaccard>=0.5), and the canonical equivalence ('controlled longitudinal study' ~ 'multi-year intervention trial') is lexically DISJOINT, so deterministic folding cannot reach it.

## Size
- Trajectories: **1525**; trajectories where folding merged >=1 direction: **80**; mean branch_redundancy_ratio: **0.0175**.

## v1 vs v1.1 vs v1.2

| signal | v1 | v1.1 | v1.2 |
| --- | --- | --- | --- |
| composite_drift ~ severity | 0.458 | 0.466 | 0.466 |
| branch entropy ~ alternative_coverage | 0.225 (lexical) | -- | 0.222 (semantic) |
| branch-collapse events (total) | 4910 (lexical) | -- | 5532 (semantic) |
| per-model rank Spearman (composite) | -- | -- | 0.8 |
| trajectory Spearman (composite~sev) | -- | -- | 0.388 |
| top-10/25/50 overlap (v1.2) | -- | -- | 0.2/0.16/0.14 |

## Class-wise semantic branch metrics

| metric | no_drift | mild_drift | trajectory_drift | trajectory_lock_in |
| --- | --- | --- | --- | --- |
| semantic_branch_entropy | 0.925 | 0.901 | 0.896 | 0.818 |
| irreversible_semantic_collapse | 0.023 | 0.037 | 0.053 | 0.059 |

## Final answers

- **Does semantic branch folding improve DriftBench alignment?** composite 0.466 (v1.1) -> 0.466 (v1.2): no material change.
- **Does it reduce fake branch diversity?** Folding merged directions in only 80/1525 trajectories (mean redundancy 0.0175) -- DriftBench's directions are already distinct, so there is little lexical redundancy to remove.
- **Does collapse become more meaningful?** semantic collapse events 5532 vs lexical 4910 (similar); branch entropy ~ alternative_coverage 0.225 -> 0.222 (not improved).
- **Is deterministic folding sufficient?** Yes for the rhetorical-variant cases it can reach, but the real equivalences in this benchmark are lexically DISJOINT paraphrases that deterministic folding cannot detect -- so it is NOT sufficient for true semantic branch diversity here.
- **Are semantic sensors now justified?** See driftbench_trace_v12_mutation_proposal.md -- lexical folding hit its ceiling; embeddings are the indicated next lever (PROPOSAL ONLY).

## DESi-core invariance
- Peripheral; reads `desi.frames` read-only; core byte-identical.

## Honesty / limits
- Deterministic lexical folding only; single LLM auditor; class-imbalanced; metrics NOT tuned on results. v1/v1.1 unchanged.
