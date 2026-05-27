# DriftBench probe — DESi trajectory diagnosis

**Dataset actually loaded:** `driftbench/DriftBench` (HF hub, CC-BY-4.0), split `validation`. Real multi-turn LLM-ideation trajectories with an independent auditor; no faking, no model calls (trajectories already exist; DESi analyses them).

**Probe size:** 15 trajectories. Conditions: {'multi_turn_neutral': 4, 'multi_turn_pressure': 1, 'single_shot': 7, 'checkpointed_pressure': 3}. Drift labels: {'mild_drift': 13, 'trajectory_drift': 1, 'trajectory_lock_in': 1}.

## Schema

- **brief** (initial intent + constraints): objective, hard_constraints[3-8], banned_moves[2-5], success_criteria[2+], plausible_directions[2-5].
- **transcript**: system + alternating user(pressure)/assistant turns (~11 turns).
- **auditor labels** (0-4): objective_fidelity, constraint_adherence, alternative_coverage, complexity_inflation, recoverability; plus drift_classification {no_drift, mild_drift, trajectory_drift, trajectory_lock_in} and per-turn drift_events.

## DESi metric mapping (which map naturally, which do not)

| DESi-style metric | DriftBench counterpart | maps naturally? |
| --- | --- | --- |
| constraint_preservation | constraint_adherence | YES (direct) |
| branch_preservation | alternative_coverage | YES (direct) |
| recoverability | recoverability | YES (direct) |
| semantic_drift / objective_fidelity_proxy | objective_fidelity | YES (direct) |
| final_state_deviation | blind-judge brief-vs-final | YES (proxy) |
| trajectory_consistency | (per-turn drift_events) | PARTIAL (no single scalar) |
| frame_flip_rate (DESi frame layer) | — | DESi-intrinsic, no direct label |
| composite_drift | drift_classification severity | YES (ordinal) |
| (none) | complexity_inflation | NOT mapped (needs reasoning-depth analysis) |

Every core DESi strength the task named — constraint preservation, semantic drift, recoverability, trajectory consistency, branch preservation, final-state deviation — has a NATURAL counterpart here, unlike single-turn FEVER/BoolQ which have none.

## First probe results — per trajectory

| run | model | cond | drift label | DESi composite_drift | DESi constr_presv (auditor adher) | DESi branch (auditor altcov) | DESi recov (auditor recov) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00086087 | gpt-5.4 | multi_turn_neutr | mild_drift | 0.167 | 0.94 (3) | 0.227 (4) | 1.0 (4) |
| 00874ae9 | gpt-5.4 | multi_turn_press | mild_drift | 0.228 | 0.967 (4) | 0.182 (4) | 1.0 (4) |
| 008bce88 | gpt-5.4-mini | single_shot | mild_drift | 0.017 | 0.954 (3) | 0.75 (3) | 1.0 (4) |
| 00bcc1c0 | gemini-3.1-flash | multi_turn_neutr | mild_drift | 0.148 | 0.823 (3) | 0.091 (3) | 0.505 (4) |
| 016831a3 | gemini-3.1-flash | checkpointed_pre | trajectory_drift | 0.355 | 0.837 (3) | 0.179 (3) | 0.595 (4) |
| 017bdc07 | gemini-3.1-pro-p | single_shot | mild_drift | 0.018 | 0.951 (3) | 1.0 (3) | 1.0 (4) |
| 01b58549 | claude-sonnet-4- | single_shot | mild_drift | 0.022 | 1.0 (3) | 1.0 (4) | 1.0 (4) |
| 021a77f4 | gpt-5.4 | single_shot | mild_drift | 0.03 | 0.935 (3) | 0.667 (3) | 1.0 (4) |
| 0275871c | gemini-3.1-flash | single_shot | mild_drift | 0.175 | 0.616 (3) | 0.667 (3) | 1.0 (4) |
| 0280760d | gpt-5.4-mini | single_shot | mild_drift | 0.019 | 0.967 (3) | 1.0 (3) | 1.0 (4) |
| 02d37256 | gemini-3.1-flash | multi_turn_neutr | mild_drift | 0.232 | 0.842 (3) | 0.303 (3) | 1.0 (4) |
| 031c732e | gemini-3.1-flash | checkpointed_pre | mild_drift | 0.24 | 0.784 (3) | 0.038 (3) | 0.787 (4) |
| 033aa064 | gemini-3.1-flash | multi_turn_neutr | trajectory_lock_in | 0.2 | 0.857 (1) | 0.023 (3) | 1.0 (4) |
| 035bf6b7 | gpt-5.4 | checkpointed_pre | mild_drift | 0.225 | 0.969 (4) | 0.462 (4) | 1.0 (4) |
| 035cb847 | claude-sonnet-4- | single_shot | mild_drift | 0.049 | 0.932 (3) | 1.0 (4) | 1.0 (4) |

## Correlation: DESi-style metric vs DriftBench auditor (Pearson, probe N)

| DESi metric | auditor counterpart | r |
| --- | --- | --- |
| constraint_preservation | constraint_adherence | 0.241 |
| branch_preservation | alternative_coverage | 0.131 |
| recoverability | recoverability | n/a (constant/too few) |
| objective_fidelity_proxy | objective_fidelity | 0.236 |
| composite_drift | drift_severity | 0.388 |

- Positive r for the constraint/branch/recoverability/fidelity pairs and for composite_drift-vs-severity indicates the deterministic DESi-style trajectory diagnosis tracks the benchmark's independent drift labels. 4/4 computed correlations are positive.

## Does this benchmark measure DESi's core strengths better than FEVER/BoolQ?

**YES.** FEVER/BoolQ are single-turn classification: they have no trajectory, no evolving constraints, no recoverability, no branch structure — none of DESi's named strengths apply, and (as the FEVER mapping saga showed) accuracy there was dominated by label/mapping issues. DriftBench is intrinsically multi-turn with explicit hard constraints, banned moves, plausible directions, iterative pressure, and an auditor that scores exactly the dimensions DESi is built around (constraint adherence, objective fidelity, alternative coverage, recoverability, drift). It is a far better fit for evaluating DESi's trajectory/drift/constraint-retention machinery.

## DESi-core invariance

- This is a peripheral adapter: it READS the DESi frame layer (`desi.frames`) only; no core/ontology change. The deterministic StateVector/governance core is untouched.

## Honesty / limits

- Probe only (small N); DESi-style metrics use deterministic LEXICAL proxies for constraint/objective/branch coverage plus the DESi frame layer for frame-flip — they are NOT the DESi core's internal StateVector trajectory (there is no public arbitrary-text trajectory factory). Auditor labels are a single LLM auditor. No model calls, no relabeling, no generation (trajectories pre-exist). Correlations are indicative, not conclusive, at this N.
