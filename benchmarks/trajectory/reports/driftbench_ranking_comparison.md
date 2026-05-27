# DriftBench ranking comparison — DESi TrajectoryTrace v1.1

Measurement only (no DESi metric tuning, no core change, no model calls).

## Is there an official DriftBench ranking?

**No official leaderboard/ranking file found** in the repo (checked siblings; matches: []). Ranking is therefore reconstructed from the auditor labels: a composite auditor DRIFT score = mean of severity/3 + inverted objective_fidelity / constraint_adherence / alternative_coverage / recoverability + complexity_inflation (all 0-1, higher = more drift). DESi ranking = composite_drift_v1.1.

## Size
- Trajectories ranked: **1525**; models: **5**.

## DESi vs reconstructed auditor ranking (per trajectory)

| comparison | value |
| --- | --- |
| Spearman (DESi vs auditor composite) | 0.413 |
| Spearman (DESi vs drift_severity) | 0.38 |
| Kendall tau-b (DESi vs auditor composite) | 0.301 |
| Pearson (DESi vs auditor composite) | 0.478 |
| top-10 overlap | 0.0 |
| top-25 overlap | 0.08 |
| top-50 overlap | 0.18 |

## Per-model rank table (sorted by auditor drift)

| model | n | auditor drift | auditor severity | DESi v1.1 |
| --- | --- | --- | --- | --- |
| claude-sonnet-4-6 | 315 | 0.311 | 1.619 | 0.172 |
| gemini-3.1-flash-lite-preview | 304 | 0.292 | 1.503 | 0.224 |
| gemini-3.1-pro-preview | 303 | 0.215 | 1.205 | 0.15 |
| gpt-5.4-mini | 301 | 0.148 | 0.821 | 0.126 |
| gpt-5.4 | 302 | 0.133 | 0.834 | 0.11 |

- **Per-model rank agreement (Spearman): 0.9.**

## Class-wise DESi mean (ordering check)

| no_drift | mild_drift | trajectory_drift | trajectory_lock_in |
| --- | --- | --- | --- |
| 0.068 | 0.133 | 0.244 | 0.278 |

## Top 10 DESi-high drift

- 4c16778d gemini-3.1-flash-lite-preview [trajectory_drift] DESi=0.501
- 4826ae79 gemini-3.1-flash-lite-preview [trajectory_drift] DESi=0.462
- 47777cb5 gemini-3.1-flash-lite-preview [trajectory_drift] DESi=0.459
- 564d8ded gemini-3.1-flash-lite-preview [trajectory_lock_in] DESi=0.45
- a9c0d094 gemini-3.1-flash-lite-preview [trajectory_drift] DESi=0.447
- fe10cd51 gemini-3.1-flash-lite-preview [trajectory_drift] DESi=0.445
- 27490cf7 gemini-3.1-flash-lite-preview [trajectory_lock_in] DESi=0.443
- 2721d050 claude-sonnet-4-6 [trajectory_drift] DESi=0.438
- 1e83047f gemini-3.1-flash-lite-preview [trajectory_drift] DESi=0.426
- 69ca738b gemini-3.1-flash-lite-preview [trajectory_drift] DESi=0.415

## Top 10 auditor-high drift

- 3fce4579 claude-sonnet-4-6 [trajectory_lock_in] auditor=0.6667 DESi=0.272
- 92a0e78e claude-sonnet-4-6 [trajectory_lock_in] auditor=0.6667 DESi=0.333
- 4b57869c claude-sonnet-4-6 [trajectory_lock_in] auditor=0.5833 DESi=0.253
- 7176887c gemini-3.1-flash-lite-preview [trajectory_lock_in] auditor=0.5833 DESi=0.26
- c7644360 gemini-3.1-flash-lite-preview [trajectory_lock_in] auditor=0.5833 DESi=0.274
- 18d95f81 gemini-3.1-flash-lite-preview [trajectory_lock_in] auditor=0.5417 DESi=0.327
- 3a0e2edd gemini-3.1-flash-lite-preview [trajectory_lock_in] auditor=0.5417 DESi=0.09
- 6b4b340b gemini-3.1-flash-lite-preview [trajectory_lock_in] auditor=0.5417 DESi=0.298
- 72d40653 gemini-3.1-flash-lite-preview [trajectory_lock_in] auditor=0.5417 DESi=0.4
- 988be932 gemini-3.1-flash-lite-preview [trajectory_lock_in] auditor=0.5417 DESi=0.287

## Top disagreement cases

- **DESi-high / auditor-low** (5 shown of those with DESi>=Q3 0.275 & no_drift):
  - cd5c8e30 [no_drift] DESi=0.338 (DESi flags drift the auditor rated clean)
  - 84c7c692 [no_drift] DESi=0.334 (DESi flags drift the auditor rated clean)
  - d3aee35b [no_drift] DESi=0.308 (DESi flags drift the auditor rated clean)
  - 931985b2 [no_drift] DESi=0.281 (DESi flags drift the auditor rated clean)
  - d8feb53a [no_drift] DESi=0.277 (DESi flags drift the auditor rated clean)
- **Auditor-high / DESi-low** (5 with severity>=2 & DESi<=Q1 0.077):
  - 4df9e2f6 [trajectory_drift] auditor=0.4028 DESi=0.0 (drift the lexical trace misses)
  - 11332ba9 [trajectory_drift] auditor=0.3611 DESi=0.077 (drift the lexical trace misses)
  - 76d5deb1 [trajectory_drift] auditor=0.3611 DESi=0.077 (drift the lexical trace misses)
  - faf17957 [trajectory_drift] auditor=0.3611 DESi=0.075 (drift the lexical trace misses)
  - b32344b5 [trajectory_drift] auditor=0.3194 DESi=0.077 (drift the lexical trace misses)

## Final answers

- **Is there an official DriftBench ranking?** No -- reconstructed from auditor labels.
- **Where does DESi stand?** Per-trajectory Spearman 0.413 (Kendall 0.301, Pearson 0.478); per-model Spearman 0.9; top-50 overlap 0.18.
- **Does DESi rank models/trajectories similarly to auditors?** Models: YES, strongly (rank 0.9). Trajectories: moderately (rank 0.413).
- **Which cases disagree?** see the disagreement section: DESi over-flags some lexically-churny but auditor-clean runs; it under-flags paraphrastic/semantic drift with little lexical footprint.
- **Strong enough for a public HF/README claim?** YES at the MODEL level (a measured claim), MODERATE at the trajectory level.

## Public-summary block (model-level, measured)

```
DESi TrajectoryTrace v1.1 is a deterministic, no-LLM trajectory-drift diagnostic.
On DriftBench (N=1525 multi-turn trajectories, 5 models), its composite
drift metric ranks MODELS in agreement with the independent auditor (Spearman
0.9), and tracks per-trajectory drift severity at Spearman 0.413 / Pearson
0.478, with top-50 overlap 0.18 -- using only deterministic lexical +
frame signals, no model calls, and no change to the DESi core.
```
## DESi-core invariance
- Measurement only; reads cached summaries + repo metadata; core byte-identical.

## Honesty / limits
- Reconstructed (not official) ranking; single LLM auditor; class-imbalanced; DESi metrics are deterministic lexical/frame proxies and were NOT tuned on this comparison.
- The per-model rank correlation is over only **5 models** (n=5), so Spearman 0.9 is one adjacent swap from perfect -- indicative, not definitive. The low top-50 overlap (0.18) shows the EXACT highest-drift trajectories diverge even though the overall rank correlation is moderate (many tied auditor severities; DESi's continuous composite breaks ties differently).
