# TrajectoryTrace v1.2 — mutation PROPOSAL (no implementation)

Deterministic semantic branch folding did not materially improve DriftBench alignment (composite 0.466 -> 0.466; branch_entropy~altcov 0.225 -> 0.222; folding merged directions in only 80/1525, mean redundancy 0.0175). NO patch applied; proposal only, requires explicit approval.

## Has lexical deterministic folding reached its ceiling?

- YES on this benchmark. DriftBench's plausible_directions are distinct by design (~1.8% lexically near), and the genuine equivalences are lexically DISJOINT paraphrases ('controlled longitudinal study' ~ 'multi-year intervention trial', Jaccard~0). Token/synonym folding cannot bridge disjoint vocabulary.
## Are embeddings / semantic sensors now justified?

- This is the FIRST place in the trajectory line where a local deterministic EMBEDDING sensor is genuinely indicated: semantic branch equivalence needs meaning, not tokens. Scope: a peripheral, deterministic, offline sentence-embedding scorer (e.g. a small MiniLM-class model IF installable and pinned) used ONLY to cluster branch alternatives; default path stays lexical if no model is available.
## What evidence is still missing

- A held-out set of human-judged branch-equivalence pairs to validate any embedding folder (precision/recall of fold decisions), and a demonstration that embedding-based folding raises branch_entropy~alternative_coverage and composite~severity WITHOUT tuning on the test labels.
## Required human approval before implementation

- No embedding model added without explicit approval, a pinned offline model + deterministic hash check, a lexical fallback, core-byte-identical regression tests, and a pre-registered evaluation showing a real gain.
