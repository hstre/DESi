# HuggingFace benchmark — run on the restored core

The semantic-flow constitution is immutable. Benchmark layers are peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi.

- source: HuggingFace-format dataset (5 tasks); extractor port: `local`; benchmark family: `SEARCH_COMPRESSION_BENCHMARK`.
- pipeline: HF loader → optional ExtractorPort (claim projections) → `benchmark_ports.input_port` → `benchmark_api` (boundary pinned) → tested adapter → replay-bound result. No core change, no new ontology.

## DESi-core metrics

| metric | value |
| --- | --- |
| tasks | 5 |
| replay stability (re-run identical) | 1.0 |
| core identity (named core vs base) | 1.0 (byte-identical) |
| governance independence | 1.0 |
| results replay-bound & traceable | 1.0 |
| critical_branch_preservation | 1.0 |
| node_reduction | 0.533333 |
| compression mode counts | `{'hard_pruning': 0, 'kept': 50, 'redundant_branch_compression': 100, 'replay_reuse': 100, 'soft_reweighting': 125}` |
| benchmark-induced mutation attempts | 5 |
| rejected core-mutation attempts | 5 |

Claims appear only as projections (extractor port output / result `claim_outputs`); the epistemic core is untouched. HF inference is optional and was not required for this run.

## Honesty / limits

- DESi-core metrics only; the search/drift metrics are intrinsic to DESi's deterministic governance (per each adapter's stated limitation), not input-scored. No truthfulness claim.
- HF hub / inference are optional; offline JSONL is the default. Any HF token is read in-process from the environment and never written to outputs.
- No core code changed; outputs secret-scanned.
