# DriftBench TrajectoryTrace v0 — per-turn DESi state tracking

Per-turn deterministic state trace (constraint activation/drop/recovery, branch collapse, content/method shift, frame flip, drift/recovery/lock-in signals) over the full DriftBench main labelled set. No model calls, no embeddings, no Neo4j, no DESi-core change (read-only frame layer).

## Size
- Trajectories traced: **1525**.
- Turn-level state records: **13709**.
- Models: 5; conditions present in data.

## Correlations: v0 summary metric vs auditor (Pearson, N=1525)

| v0 metric | auditor dim | expected | r |
| --- | --- | --- | --- |
| composite_drift_v0 | drift_severity | + | 0.407 |
| min_constraint_preservation | constraint_adherence | + | 0.227 |
| branch_preservation_proxy | alternative_coverage | + | -0.021 |
| recoverability_proxy | recoverability | + | 0.047 |
| final_objective_fidelity_proxy | objective_fidelity | + | 0.209 |
| lock_in_proxy | drift_severity | + | 0.291 |

- **Strongest match:** composite_drift_v0~drift_severity (r=0.407).
- **Turn-level vs coarse end-state:** composite_drift_v0~drift_severity r=0.407 vs the coarse full-run composite_drift~drift_severity r=0.346 (IMPROVED).

## Class-wise v0 metric averages (by auditor drift_classification)

| metric | no_drift | mild_drift | trajectory_drift | trajectory_lock_in |
| --- | --- | --- | --- | --- |
| n | 140 | 986 | 352 | 47 |
| composite_drift_v0 | 0.161 | 0.239 | 0.352 | 0.34 |
| min_constraint_preservation | 0.975 | 0.871 | 0.7 | 0.678 |
| constraints_dropped_total | 0.286 | 1.452 | 3.699 | 4.17 |
| constraints_recovered_total | 0.257 | 1.383 | 3.398 | 3.894 |
| lock_in_proxy | 0.004 | 0.016 | 0.031 | 0.036 |

## Per-model drift ranking (auditor vs v0)

| model | n | auditor drift | v0 composite_drift |
| --- | --- | --- | --- |
| claude-sonnet-4-6 | 315 | 1.619 | 0.288 |
| gemini-3.1-flash-lite-preview | 304 | 1.503 | 0.253 |
| gemini-3.1-pro-preview | 303 | 1.205 | 0.284 |
| gpt-5.4 | 302 | 0.834 | 0.225 |
| gpt-5.4-mini | 301 | 0.821 | 0.255 |

- Per-model Spearman (auditor vs v0): 0.5.

## Constraint decay / recovery / lock-in detection

- Trajectories with >=1 detected drift turn: 0.816 of 1.0.
- Trajectories with >=1 detected recovery turn: 0.408 of 1.0.
- Mean constraints dropped by class: {'no_drift': 0.286, 'mild_drift': 1.452, 'trajectory_drift': 3.699, 'trajectory_lock_in': 4.17} -- rises with auditor severity (decay detected).
- lock_in_proxy by class: {'no_drift': 0.004, 'mild_drift': 0.016, 'trajectory_drift': 0.031, 'trajectory_lock_in': 0.036} -- peaks at trajectory_lock_in (lock-in detected).

## Agreements & disagreements

- Top-10 v0-drift: 47d4fe42(trajectory_drift), 9b9c27b0(trajectory_drift), b2e6d006(mild_drift), 4ca9718c(mild_drift), e220ffbc(mild_drift), 17cb9fac(mild_drift), 40cb55bc(trajectory_lock_in), 53ab2cc6(trajectory_drift), 28f7ef7a(mild_drift), ee97745c(mild_drift).
- Top-10 auditor-drift: 033aa064(trajectory_lock_in), 18d95f81(trajectory_lock_in), 3a0e2edd(trajectory_lock_in), 3fce4579(trajectory_lock_in), 4b57869c(trajectory_lock_in), 5a59048d(trajectory_lock_in), 68ae1038(trajectory_lock_in), 6b4b340b(trajectory_lock_in), 7176887c(trajectory_lock_in), 72d40653(trajectory_lock_in).
- DESi-high / auditor-low (>=Q3 0.349 but no_drift): 8.
- Auditor-high / DESi-low (>=trajectory_drift but <=Q1 0.153): 2.

## Answers

- **Does turn-level tracing improve correlation vs the probe?** composite_drift_v0~severity r=0.407 vs coarse full-run r=0.346: YES, modest improvement.
- **Which trace metric is strongest?** composite_drift_v0~drift_severity (|r|=0.407).
- **Does DESi detect constraint decay over turns?** Yes -- mean constraints dropped rises with auditor drift class, and per-turn constraints_dropped events are recorded.
- **Does DESi detect recoveries after drift?** 0.408 of trajectories have explicit recovery turns (constraints re-activating after being dropped) -- a signal the coarse end-state metric could not express.
- **Does DESi detect lock-in better than end-state metrics?** lock_in_proxy peaks at trajectory_lock_in -- the per-turn 'dropped-and-stuck' signal gives a dedicated lock-in indicator the end-state composite lacked.
- **Which failure modes remain invisible to deterministic tracing?** Paraphrastic constraint satisfaction/violation (a constraint honoured in different words reads as 'dropped'), semantic (non-lexical) objective drift, and subtle reasoning-quality / complexity-inflation that has no lexical footprint -- these need embeddings or a model judge, deliberately excluded here.
- **Is Neo4j needed now, or is JSONL enough?** JSONL is sufficient for v0: the trace is a per-turn record stream with simple transition deltas; there is no cross-trajectory graph query need yet. Defer Neo4j until multi-trajectory state-graph queries (shared drift motifs, branch lineage across runs) are actually required.

## DESi-core invariance
- Peripheral; reads `desi.frames` read-only; core byte-identical; no ontology change.

## Honesty / limits
- Deterministic LEXICAL trace + read-only frame layer; not the core StateVector trajectory. Auditor labels are a single LLM auditor; classes are imbalanced (mostly mild_drift). Correlations bounded by proxy fidelity. No model calls, no relabeling, no generation.
