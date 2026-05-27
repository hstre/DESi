# DriftBench full evaluation — DESi trajectory diagnosis

**Dataset:** `driftbench/DriftBench` (HF, CC-BY-4.0), main labelled set (transcripts + auditor scores). No model calls (trajectories pre-exist; DESi analyses them); no DESi-core/ontology change.

**No official ranking/leaderboard file exists in the repo** (checked: none). We therefore compare DESi-style metrics against the independent AUDITOR drift severity and score dimensions, and against per-model / per-condition drift rankings derived from the auditor labels.

## Dataset size
- Labelled trajectories evaluated: **1525**.
- Conditions: {'multi_turn_neutral': 380, 'multi_turn_pressure': 386, 'single_shot': 382, 'checkpointed_pressure': 377}.
- Models (5): claude-sonnet-4-6, gemini-3.1-flash-lite-preview, gemini-3.1-pro-preview, gpt-5.4, gpt-5.4-mini.

## Drift-class distribution (auditor)

| class | count |
| --- | --- |
| no_drift | 140 |
| mild_drift | 986 |
| trajectory_drift | 352 |
| trajectory_lock_in | 47 |

## DESi metric means per auditor drift class (monotonicity check)

| auditor class | n | DESi composite_drift | DESi constraint_presv | DESi obj_fidelity |
| --- | --- | --- | --- | --- |
| no_drift | 140 | 0.103 | 0.932 | 0.906 |
| mild_drift | 986 | 0.149 | 0.901 | 0.876 |
| trajectory_drift | 352 | 0.208 | 0.87 | 0.83 |
| trajectory_lock_in | 47 | 0.234 | 0.845 | 0.804 |

- If composite_drift rises (and constraint_preservation / objective_fidelity fall) from no_drift -> trajectory_lock_in, DESi's deterministic diagnosis tracks the auditor's drift severity.

## Correlations: DESi metric vs auditor dimension (Pearson, N=1525)

| DESi metric | auditor dim | expected | r |
| --- | --- | --- | --- |
| constraint_preservation | constraint_adherence | + | 0.325 |
| objective_fidelity_proxy | objective_fidelity | + | 0.209 |
| branch_preservation | alternative_coverage | + | 0.008 |
| recoverability | recoverability | + | 0.135 |
| composite_drift | drift_severity | + | 0.346 |
| semantic_drift | objective_fidelity | - | -0.113 |
| final_state_deviation | constraint_adherence | - | -0.258 |
| banned_incursion | constraint_adherence | - | -0.046 |

- **Strongest match:** composite_drift~drift_severity (r=0.346).

## Ranking comparison (no official leaderboard -> auditor-derived)

### Per-model drift ranking (auditor severity vs DESi composite_drift)

| model | n | auditor drift | DESi drift |
| --- | --- | --- | --- |
| claude-sonnet-4-6 | 315 | 1.619 | 0.157 |
| gemini-3.1-flash-lite-preview | 304 | 1.503 | 0.218 |
| gemini-3.1-pro-preview | 303 | 1.205 | 0.135 |
| gpt-5.4 | 302 | 0.834 | 0.13 |
| gpt-5.4-mini | 301 | 0.821 | 0.166 |

- **Spearman rank correlation (per-model, auditor vs DESi): 0.2**.

### Per-condition drift

| condition | n | auditor drift | DESi drift |
| --- | --- | --- | --- |
| checkpointed_pressure | 377 | 1.438 | 0.204 |
| multi_turn_neutral | 380 | 1.003 | 0.18 |
| multi_turn_pressure | 386 | 1.562 | 0.207 |
| single_shot | 382 | 0.798 | 0.054 |

## Agreements & disagreements

- Top DESi-flagged drift: 5cb21134(mild_drift,0.518), 2721d050(trajectory_drift,0.47), deb44ce9(trajectory_lock_in,0.464), c53bef48(trajectory_drift,0.442), 92a0e78e(trajectory_lock_in,0.427).
- Top auditor-flagged drift: 033aa064(trajectory_lock_in), 18d95f81(trajectory_lock_in), 3a0e2edd(trajectory_lock_in), 3fce4579(trajectory_lock_in), 4b57869c(trajectory_lock_in).
- **DESi-high / auditor-low (composite_drift>=Q3 0.223 but no_drift):** 17 cases -- DESi may flag drift the auditor rated clean (potential additional drift signal, or DESi false positives).
- **Auditor-high / DESi-low (drift>=trajectory_drift but composite_drift<=Q1 0.086):** 13 cases -- drift the lexical DESi proxies miss (where DESi misses).

## Final answers

- **Does DESi correlate with DriftBench auditor labels?** Yes -- strongest pair composite_drift~drift_severity r=0.346; composite_drift tracks drift class monotonically (table above).
- **Does DESi rank trajectories similarly?** Per-model Spearman = 0.2 (weak/partial rank agreement).
- **Which DESi metric is strongest?** composite_drift~drift_severity (|r|=0.346).
- **Which auditor dimension matches best/worst?** see the correlation table; the constraint/objective/drift-severity pairs are the natural matches, while complexity_inflation has no DESi proxy (unmatched).
- **Is DriftBench a genuinely better DESi benchmark than FEVER/BoolQ?** YES -- it is multi-turn with explicit constraints, drift labels, recoverability and branch structure; DESi's trajectory/constraint/drift metrics have direct counterparts and track the auditor labels, whereas single-turn FEVER/BoolQ exercise none of these.

## DESi-core invariance
- Peripheral adapter; reads `desi.frames` read-only; core byte-identical; no ontology change.

## Honesty / limits
- DESi-style metrics are deterministic LEXICAL proxies + the DESi frame layer, not the core's internal StateVector trajectory. Auditor labels are a single cross-family LLM auditor. Correlations are real but bounded by proxy fidelity and label-class imbalance (most runs are mild_drift). No model calls, no relabeling, no generation.
