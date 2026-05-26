# HF cross-benchmark summary — restored core

The semantic-flow constitution is immutable. Benchmark layers are peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi.

## Per-dataset DESi-core metrics

| dataset | examples | replay | core id | gov | crit_pres | node_red | hard_prune | mut rej | errors | elapsed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `google/boolq` (validation) | 100 | 1.0 | 1.0 | 1.0 | 1.0 | 0.533333 | 0 | 5/5 | 0 | 2.0s |
| `BeIR/scifact` (queries) | 100 | 1.0 | 1.0 | 1.0 | 1.0 | 0.533333 | 0 | 5/5 | 0 | 2.0s |
| `truthfulqa/truthful_qa` (validation) | 817 | 1.0 | 1.0 | 1.0 | 1.0 | 0.533333 | 0 | 5/5 | 0 | 2.1s |

## Cross-dataset questions

- **Replay-stable across external datasets?** YES — every dataset's re-run was byte-identical.
- **Does benchmark input alter core behavior?** NO — the DESi-core metrics (critical_branch_preservation, node_reduction, novelty/quality preservation) are identical across TruthfulQA, BoolQ and SciFact, and core identity held; the input changes only which projections are recorded, not the core's behavior.
- **Unresolved / recoverability markers (branch loss)?** NONE — hard_pruning = 0 on every dataset (no critical-branch loss).
- **Metrics stable across datasets:** replay_stable, core_identity_ok, gov_independent, critical_branch_preservation, node_reduction, novelty_preservation, quality_preservation, hard_pruning.
- **Metrics that are benchmark-specific:** dataset id / config / split, examples loaded & mapped, elapsed time, and the recorded claim projections — i.e. only the input metadata, never a core guarantee.
- **Mutation rejection across datasets:** all refused.

## Verdict

- HF benchmarking is genuinely operational on the restored core: real external datasets run through the tested benchmark ports with no core change.
- DESi remained architecturally invariant: identical core metrics and byte-identical core across all datasets is the evidence that benchmark input tests DESi without redefining it.

## Honesty / limits

- DESi-core metrics only; intrinsic to DESi's deterministic governance, so uniformity across datasets is expected and is itself the input-invariance evidence — not a per-example score.
- Larger public runs are bounded by HF hub rate limits (unauthenticated) and dataset-format support (script-based datasets such as the canonical allenai/scifact do not load under datasets>=4); these are periphery concerns, not core limits.
