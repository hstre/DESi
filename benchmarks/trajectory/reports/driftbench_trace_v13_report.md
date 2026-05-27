# DriftBench TrajectoryTrace v1.3 — semantic-sensor branch folding

Branch directions folded by the pinned sensor (`minishlab/potion-base-8M`, deterministic, offline) at the probe-FROZEN threshold **0.31** (probe F1 0.917, precision 1.0, recall 0.846; selected on the held-out probe, NOT on DriftBench). Everything else is v1.1. No core change.

## Size
- Trajectories: **1525**; briefs whose directions the sensor merged: **35/38**.

## v1.1 vs v1.2 (lexical fold) vs v1.3 (semantic-sensor fold)

| signal | v1 / v1.1 | v1.2 (lexical) | v1.3 (sensor) |
| --- | --- | --- | --- |
| composite_drift ~ severity | 0.466 (v1.1) | -- | 0.356 |
| branch entropy ~ alternative_coverage | 0.225 (v1 lexical) | 0.222 | 0.031 |
| mean branch redundancy (folding amount) | -- | 0.0175 | 0.5625 |
| branch preservation ~ alternative_coverage | -- | -- | -0.054 |
| per-model rank Spearman (composite) | -- | -- | 0.8 |
| trajectory Spearman (composite~sev) | -- | -- | 0.328 |
| top-10/25/50 overlap (v1.3) | -- | -- | 0.0/0.04/0.08 |

## Final answers

- **Was an embedding sensor available?** YES -- `minishlab/potion-base-8M` (model2vec static, deterministic, offline; no torch).
- **Did the held-out probe justify the threshold?** YES -- threshold 0.31 at probe F1 0.917 (precision 1.0, recall 0.846), fixed before DriftBench.
- **Did v1.3 improve branch preservation?** branch entropy ~ alternative_coverage 0.225 (lexical) -> 0.031 (sensor): NOT improved. The sensor merged directions in 35/38 briefs (mean redundancy 0.5625 vs lexical 0.0175).
- **Did overall DriftBench alignment improve?** composite 0.466 (v1.1) -> 0.356 (v1.3): dropped.
- **Did semantic sensing add useful information beyond deterministic v1.1?** NO material improvement over deterministic v1.1 on this benchmark.
- **Keep as optional peripheral sensor or reject?** REJECT for DriftBench branch folding: at the probe-frozen threshold the sensor OVER-FOLDS DriftBench's distinct same-domain directions (35/38 briefs, redundancy ~0.56), collapsing real branch diversity and dropping composite 0.466->0.356. The probe threshold does not transfer (DriftBench directions are same-domain and exceed it); per the rule it was NOT re-tuned on DriftBench. The sensor + probe remain available for benchmarks with genuinely paraphrastic, cross-domain branches.

## DESi-core invariance
- Peripheral; sensor is offline static embeddings; reads `desi.frames` read-only; core byte-identical; no ontology change.

## Honesty / limits
- Threshold fixed on the held-out probe (not DriftBench); static embeddings miss the hardest disjoint paraphrases (probe recall 0.846); v1/v1.1 unchanged; no auditor-label tuning; deterministic.
