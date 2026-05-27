# DriftBench TrajectoryTrace v1.1 — fixing the two weak metrics

Targeted, side-by-side periphery fixes (v1 unchanged): (A) irreversible lock-in now based on SUSTAINED unrecovered constraint loss + no-recovery-after-collapse + objective-stuck-low + late narrowing (was branch-collapse-only); (B) method/content divergence now separates a rhetorical MODE axis (scientific vs persuasive tokens) from a content/objective axis (objective + constraint overlap decline). Deterministic; no LLM/embeddings/Neo4j; DESi-core read-only.

## Size
- Trajectories: **1525**.

## What changed & headline comparison (correlation with auditor drift_severity)

| signal | v1 | v1.1 |
| --- | --- | --- |
| composite_drift ~ severity | 0.458 | 0.466 |
| irreversible_lock_in ~ severity | 0.075 | 0.255 |
| method/content divergence ~ severity | 0.266 | 0.213 |

- **Lock-in detection improved?** YES (r 0.075 -> 0.255).
- **Method/content less noisy?** YES -- method vs content redundancy dropped from corr=0.94 (v1, near-duplicate) to corr=0.088 (v1.1, orthogonal axes). method_drift_v11 ~ objective_fidelity r=-0.065 (more method drift -> lower fidelity).
- **Composite improved?** YES (r 0.458 -> 0.466). Per-model rank (v1.1): Spearman 0.8.

## Lock-in class separation (mean proxy by auditor class)

| version | no_drift | mild_drift | trajectory_drift | trajectory_lock_in | false-neg on lock_in |
| --- | --- | --- | --- | --- | --- |
| v1 (branch-only) | 0.023 | 0.037 | 0.054 | 0.059 | 40/47 |
| v1.1 (sustained) | 0.067 | 0.096 | 0.143 | 0.11 | 0/47 |

- v1.1 lock-in broadly increases with class; false negatives on the lock_in class fell 40 -> 0 of 47.

## Method vs content (orthogonality)

- v1: method_total vs content_total corr = 0.94 (redundant -> divergence was noise).
- v1.1: method_drift vs content_drift corr = 0.088 (separated axes).
| class | method_drift_v11 | content_drift_v11 | divergence_v11 |
| --- | --- | --- | --- |
| no_drift | 0.001 | 0.016 | 0.016 |
| mild_drift | 0.01 | 0.023 | 0.027 |
| trajectory_drift | 0.012 | 0.053 | 0.054 |
| trajectory_lock_in | 0.005 | 0.046 | 0.048 |

## Final answers

- **Did lock-in detection improve?** YES (severity r 0.075 -> 0.255; false-neg 40 -> 0/47).
- **Did method/content divergence improve?** YES (redundancy 0.94 -> 0.088; the axes are now orthogonal so the signal is interpretable, even if its direct severity correlation stays modest).
- **Did overall DriftBench alignment improve?** composite r 0.458 -> 0.466 (improved).
- **Is v1.1 worth keeping?** YES -- the lock-in fix alone materially improves a previously-broken metric, and the divergence axes are now meaningful.
- **Is mutation justified now?** NO -- the periphery fix worked; DESi-core stays untouched.

## DESi-core invariance
- Peripheral; reads `desi.frames` read-only; core byte-identical.

## Honesty / limits
- Deterministic lexical/mode + frame signals; single LLM auditor; class-imbalanced (mostly mild_drift). v1 metrics unchanged. No model calls, no relabeling.
