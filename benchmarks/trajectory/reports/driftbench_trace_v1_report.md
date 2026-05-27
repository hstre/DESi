# DriftBench TrajectoryTrace v1 — trajectory dynamics

Per-turn drift-event ledger + transition-level state, plus per-trajectory dynamics (constraint half-life, recovery quality, branch entropy/collapse, method-vs-content drift, cumulative drift energy). Deterministic; no LLM/embeddings/Neo4j; DESi-core read-only.

## Size
- Trajectories: **1525**; turn records: **13709**; models: 5.

## v0 vs v1 (composite_drift ~ drift_severity, matched set)

- v0 (end-state composite): r=0.407
- v1 (dynamics composite): r=0.458
- **Turn-dynamics IMPROVE correlation (+0.051).**

## v1 metric correlations vs auditor (Pearson, N=1525)

| v1 metric | auditor dim | exp | r |
| --- | --- | --- | --- |
| composite_drift_v1 | drift_severity | + | 0.458 |
| constraint_half_life_mean | constraint_adherence | + | 0.24 |
| recovery_quality_proxy | recoverability | + | 0.207 |
| irreversible_lock_in_proxy | drift_severity | + | 0.075 |
| cumulative_drift_energy | drift_severity | + | 0.373 |
| branch_entropy_proxy | alternative_coverage | + | 0.225 |
| divergence_between_method_and_content | objective_fidelity | - | -0.091 |

- Strongest: composite_drift_v1~drift_severity (r=0.458); weakest: irreversible_lock_in_proxy~drift_severity (r=0.075).

## Class-wise v1 dynamics (by auditor drift_classification)

| metric | no_drift | mild_drift | trajectory_drift | trajectory_lock_in |
| --- | --- | --- | --- | --- |
| n | 140 | 986 | 352 | 47 |
| composite_drift_v1 | 0.06 | 0.123 | 0.229 | 0.27 |
| constraint_half_life_mean | 0.994 | 0.978 | 0.945 | 0.932 |
| recovery_quality_proxy | 0.924 | 0.696 | 0.28 | 0.133 |
| irreversible_lock_in_proxy | 0.023 | 0.037 | 0.054 | 0.059 |
| cumulative_drift_energy | 1.767 | 2.837 | 4.238 | 4.3 |
| branch_entropy_proxy | 0.926 | 0.904 | 0.898 | 0.834 |
| divergence_method_content | 0.047 | 0.104 | 0.154 | 0.125 |

## Per-model rank (auditor vs v1): Spearman 0.8

- claude-sonnet-4-6: auditor 1.619, v1 0.156
- gemini-3.1-flash-lite-preview: auditor 1.503, v1 0.218
- gemini-3.1-pro-preview: auditor 1.205, v1 0.141
- gpt-5.4: auditor 0.834, v1 0.098
- gpt-5.4-mini: auditor 0.821, v1 0.115

## Recovery: fake vs real

- operational (real) recoveries: **79**; rhetorical (fake) recoveries: **1364**. DESi distinguishes them by requiring objective overlap to stabilise and banned-move pressure not to rise at the recovery turn -- the 'recall-adherence dissociation' DriftBench documents.
- recovery_quality_proxy by class: no_drift 0.924, mild_drift 0.696, trajectory_drift 0.28, trajectory_lock_in 0.133.

## Notable trajectories

- Top-10 cumulative_drift_energy: 554f53f1(mild_drift,6.744), 532eeeb8(mild_drift,6.472), ee6c3c7a(mild_drift,6.466), 3c6ad174(trajectory_drift,6.163), 25bb8e7f(trajectory_drift,6.125), 870bfbff(mild_drift,6.093), 75736321(mild_drift,6.065), 77e6e296(trajectory_lock_in,6.032), 072c4bf4(trajectory_drift,6.0), b51680c3(mild_drift,5.999).
- Successful (operational) recovery, fully recovered: 10 found: 07598753(trajectory_drift), 0c088582(trajectory_drift), 28b2337e(no_drift), 2a610a80(mild_drift), 2cff2979(mild_drift), 4111dd5e(mild_drift), 51efaa26(trajectory_drift), 584693e2(mild_drift), 5bc2f4b6(mild_drift), 679c85fd(mild_drift).
- Irreversible branch collapse: 10 (top: 93b963d9(trajectory_drift,1.0), 174d6da8(trajectory_lock_in,0.75), 1909c602(mild_drift,0.75), 258f4762(trajectory_drift,0.75), 39f1b3a3(mild_drift,0.75)).

## Final answers

- **Is DESi becoming more trajectory-aware?** Yes -- v1 records per-turn drift events, transition deltas, constraint half-lives and recovery QUALITY that v0 could not express.
- **Which dynamics matter most for drift detection?** composite_drift_v1~drift_severity (strongest, r=0.458); constraint half-life and cumulative drift energy carry the dynamics signal.
- **Is branch collapse now measurable?** Yes -- branch_entropy_proxy, branch_collapse_events and irreversible_lock_in_proxy (10 irreversible-collapse trajectories detected).
- **Can DESi distinguish fake recovery from real recovery?** Yes -- operational vs rhetorical split (79 operational vs 1364 rhetorical); recovery_quality_proxy tracks auditor recoverability (table).
- **Is JSONL still sufficient?** Yes -- per-turn ledger + transition deltas are a flat record stream; no cross-trajectory graph queries yet. Neo4j stays deferred.
- **Is mutation now justified?** NO -- v1 already improves correlation within the periphery; no core change needed.

## DESi-core invariance
- Peripheral; reads `desi.frames` read-only; core byte-identical.

## Honesty / limits
- Deterministic lexical+frame dynamics, not the core StateVector trajectory; single LLM auditor; class-imbalanced. No model calls, no relabeling.
