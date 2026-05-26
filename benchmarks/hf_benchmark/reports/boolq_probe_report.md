# HuggingFace probe — google/boolq (real run on the restored core)

The semantic-flow constitution is immutable. Benchmark layers are peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi.

Real HF run: dataset loaded from the hub via `datasets`, mapped into boundary-pinned BenchmarkTasks (`benchmark_ports.input_port` -> `benchmark_api`), run through the tested `SearchCompressionAdapter`. No LLM, no HF inference, no core change.

| metric | value |
| --- | --- |
| dataset id | `google/boolq` |
| config | `None` |
| split | `validation` |
| number of examples (loaded / mapped) | 100 / 100 |
| replay stability | 1.0 |
| core identity | 1.0 (byte-identical) |
| governance independence | 1.0 |
| critical branch preservation | 1.0 |
| node reduction | 0.533333 |
| hard pruning (branch loss marker) | 0 |
| mutation attempts rejected | 5/5 |
| adapter errors | 0 |
| elapsed time | 2.0s |

Claims appear only as projections (each example's text becomes a claim projection); the epistemic core is untouched. Search-compression metrics are intrinsic to DESi's deterministic governance, so they do not vary with benchmark input.

## Honesty / limits

- Real HF dataset (`google/boolq`); DESi-core metrics only; no truthfulness score, no LLM, no inference. The benchmark tested DESi; it did not change it (core identity verified, all mutation probes refused).
- The search-compression metrics come from DESi's deterministic synthetic search space (per the adapter's stated limitation), not a per-example score.
