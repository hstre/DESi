# DESi Context Compression Demo — DriftBench

Replace each raw multi-turn transcript with a compact DESi v1.1 STATE summary (constraint preservation + recovery quality + lock-in + branch state + drift-event ledger + composite) and ask: how many tokens are saved, and is drift still detectable from the compact state? Token counter: `model2vec/potion-base-8M` (offline, deterministic). No LLM, no core change.

## Token savings (N=1525)

| metric | mean | median |
| --- | --- | --- |
| raw transcript tokens | 9900 | 8856 |
| DESi state tokens | 269 | 320 |
| compression ratio (tokens saved) | 0.965 | 0.965 |

- **Is 70-90% savings realistic?** 0/1525 trajectories (0%) land in the 70-90% band; 1525/1525 (100%) exceed 90%. Mean savings **96%** (median 96%).

## Drift detection: raw proxy (A) vs DESi summary (B)

- A (raw transcript proxy, first-vs-last lexical drift) ~ auditor severity: r=0.438.
- B (DESi compact-state composite drift) ~ auditor severity: r=0.466.
- **drift_score_preservation (B/A): 1.06** -- the compact state detects drift as well as or better than the raw transcript, at a fraction of the tokens.

## Signal preservation (compact state carries each drift signal explicitly)

| signal | preserved fraction |
| --- | --- |
| constraint_preservation_preserved | 1.0 |
| recovery_events_preserved | 1.0 |
| lock_in_preserved | 1.0 |
| branch_state_preserved | 1.0 |
- Compression is to a STRUCTURED state, not lossy text truncation: the v1.1 drift signals are retained as explicit scalars + a per-turn event ledger.

## 10 best (highest compression)

| run | model | drift | raw_tok | desi_tok | ratio |
| --- | --- | --- | --- | --- | --- |
| 32f0d551 | claude-sonnet- | trajectory_drift | 31848 | 330 | 0.99 |
| 50196f94 | claude-sonnet- | trajectory_drift | 30520 | 348 | 0.989 |
| 58dad462 | claude-sonnet- | trajectory_drift | 30618 | 348 | 0.989 |
| 76f27683 | claude-sonnet- | trajectory_drift | 30259 | 326 | 0.989 |
| 88bf16e1 | claude-sonnet- | trajectory_lock_in | 29615 | 333 | 0.989 |
| 071a7bc4 | claude-sonnet- | trajectory_drift | 29912 | 360 | 0.988 |
| 072c4bf4 | claude-sonnet- | trajectory_drift | 28815 | 355 | 0.988 |
| 08ab870d | claude-sonnet- | trajectory_drift | 28191 | 335 | 0.988 |
| 18360f8a | claude-sonnet- | trajectory_drift | 31419 | 366 | 0.988 |
| 1ee3d759 | claude-sonnet- | mild_drift | 27781 | 347 | 0.988 |

## 10 worst (lowest compression)

| run | model | drift | raw_tok | desi_tok | ratio |
| --- | --- | --- | --- | --- | --- |
| f6fdb364 | gemini-3.1-fla | mild_drift | 1032 | 87 | 0.916 |
| ad0e6e14 | gemini-3.1-fla | mild_drift | 1061 | 87 | 0.918 |
| c04b2c6f | gemini-3.1-fla | mild_drift | 1125 | 87 | 0.923 |
| 0755dbd7 | gemini-3.1-fla | mild_drift | 1113 | 85 | 0.924 |
| 0abbbfa8 | gemini-3.1-pro | no_drift | 1120 | 85 | 0.924 |
| fb4c7e88 | gemini-3.1-fla | mild_drift | 1114 | 85 | 0.924 |
| cd91e3ca | gemini-3.1-fla | mild_drift | 1138 | 85 | 0.925 |
| c03f0272 | gemini-3.1-fla | mild_drift | 1157 | 85 | 0.927 |
| a5b0ef06 | gemini-3.1-fla | mild_drift | 1212 | 87 | 0.928 |
| dbc029a6 | gpt-5.4-mini | no_drift | 1182 | 85 | 0.928 |

## Does DriftBench drift detection remain stable after compression?

**Yes.** The compact DESi state preserves (and here exceeds) the raw-transcript drift signal's alignment with the auditor while removing ~96% of the tokens -- drift detection is stable under compression.

## Honesty / limits

- Token counts use a static tokenizer as a deterministic proxy; the raw-drift proxy (A) is a cheap first-vs-last lexical signal, not a full re-derivation; signal 'preservation' means the compact state carries each field explicitly (it is a structured summary, so by construction lossless for those signals). No core change, no LLM, no auditor-label tuning.
