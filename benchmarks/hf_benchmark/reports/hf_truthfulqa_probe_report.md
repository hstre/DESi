# HuggingFace probe — truthfulqa/truthful_qa (real run on the restored core)

The semantic-flow constitution is immutable. Benchmark layers are peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi.

This is a REAL HuggingFace run: the dataset was loaded from the hub via the `datasets` library, mapped into boundary-pinned BenchmarkTasks (`benchmark_ports.input_port` -> `benchmark_api`), and run through the tested `SearchCompressionAdapter`. No LLM, no HF inference, no core change.

## Run metrics

| metric | value |
| --- | --- |
| dataset name | `truthfulqa/truthful_qa` |
| config | `generation` |
| split | `validation` |
| question / answer field | `question` / `best_answer` |
| examples loaded (real HF) | 20 |
| examples mapped to BenchmarkTask | 20 |
| real HF run (not offline sample) | yes |
| replay stability (re-run identical) | 1.0 |
| core identity (named core vs base) | 1.0 (byte-identical) |
| governance independence | 1.0 |
| results replay-bound & traceable | 1.0 |
| critical_branch_preservation (DESi-preservation) | 1.0 |
| node_reduction | 0.533333 |
| novelty_preservation | 1.0 |
| quality_preservation | 1.0 |
| adapter errors | 0 |
| benchmark-induced mutation attempts | 5 |
| rejected core-mutation attempts (no core mutation) | 5/5 |
| elapsed time | 1.9s |

Claims appear only as projections (each example's answer becomes a claim projection / the result's `claim_outputs`); the epistemic core is untouched. The search-compression metrics are intrinsic to DESi's deterministic governance, so they are uniform across the 20 examples — that uniformity is the replay-stability evidence.

## Load attempts (transparency)

| dataset[config] | result |
| --- | --- |
| `truthfulqa/truthful_qa[generation]` | OK |

## Honesty / limits

- Real HF dataset load; DESi-core metrics only; no truthfulness score, no LLM, no HF inference. The benchmark tested DESi; it did not change it (core identity verified, all mutation probes refused).
- The search-compression metrics come from DESi's deterministic synthetic search space (per the adapter's stated limitation), not a per-example score.
- No core code changed; no secrets; outputs are benchmark periphery.
