# Restored-core 100-task benchmark — comparison vs P31/P32

The semantic-flow constitution is immutable. Benchmark layers are peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi.

## A) Tasks / benchmark source

- 100 tasks: the TruthfulQA limit-100 set (`tqa-0000..tqa-0099`) — the SAME 100 tasks the P31/P32 role-correct run used. Stored as clean benchmark INPUT (`benchmarks/restored_core_100/tasks_100.jsonl`: task_id + question + answer only; the P20–P33 `desi_metadata`/`static_eval` fields were deliberately stripped). The dataset is benchmark periphery, not core.

## B) Pipeline that actually ran

- INPUT port: `desi.benchmark_ports.input_port` → `benchmark_api.make_task` (pins the full protected-core forbidden boundary; the caller cannot widen it).
- ADAPTER: the tested `desi.benchmark_api_search.SearchCompressionAdapter` (existing core search-compression metrics; no new logic).
- RUNNER: `desi.benchmark_ports.BenchmarkRunner` (pure orchestration).
- OUTPUT port: replay-bound `BenchmarkResult` → serialized record.
- NO core mutation: `make_task` pins the boundary and the adapter refuses any steering task (see E). No new ontology, no new heuristics, no API calls.

## C) DESi-core metrics (restored core) vs P31/P32 (claim-centric)

### Restored-core run (DESi-core metrics)

| DESi-core metric | value |
| --- | --- |
| tasks run | 100/100 |
| replay stability (re-run byte-identical) | 1.0 |
| core identity (named core vs base) | 1.0 (byte-identical) |
| governance independence (all tasks) | 1.0 |
| results replay-bound & traceable | 1.0 |
| critical_branch_preservation | 1.0 |
| node_reduction | 0.533333 |
| branch_compression | 0.866667 |
| novelty_preservation | 1.0 |
| quality_preservation | 1.0 |
| compute_reduction | 0.533333 |
| compression mode counts (routed/folded/preserved) | `{'hard_pruning': 0, 'kept': 1000, 'redundant_branch_compression': 2000, 'replay_reuse': 2000, 'soft_reweighting': 2500}` |
| benchmark-induced mutation attempts | 10 |
| rejected core-mutation attempts | 10 |
| per-task metrics uniform (intrinsic, replay-stable) | True |

The search-compression metrics are *intrinsic* to DESi's deterministic search governance, so they are identical across all 100 tasks — that uniformity IS the replay-stability evidence. The benchmark measures whether DESi preserves critical branches and stays unsteerable, not an input-scored quantity.

### P31/P32 reference (claim-centric run)

| P31/P32 metric | value | DESi-core-conform? |
| --- | --- | --- |
| coverage (≥1 claim) | 72/100 | partial (extractor coverage, periphery) |
| empty answers | 28/100 | n/a (input property) |
| folded single-builder | 57 | NO (claim-folding, not core) |
| escalated → DBA | 15/100 | NO (claim-DBA load, not core) |
| DBA semantic_reconcilable | 7 | NO (reconciliation, not core) |
| DBA protected_branch | 3 | partial (maps to branch preservation) |
| DBA logical_polarity_conflict | 5 | partial (conflict hold) |
| close / branch | 7 / 8 | NO (claim outcomes, not core) |
| P32 branches before→after | 8→1 | NO (claim-fold tuning, not core) |
| role-correct cost estimate | $0.0158 (~84% vs dual) | adapter-layer estimate |

- Where the restored core is **better**: it reports the metrics DESi was built to guarantee — replay stability, core identity, governance independence, critical-branch preservation, mutation rejection — which the P31/P32 claim run did **not** measure at all.
- Where P31/P32 looks **better/richer**: it produces input-dependent claim-level numbers (coverage, reconciliation, branch reduction 8→1, cost). Per the evaluation rule, these are **not** DESi-core metrics: fewer branches / more reconciliation / more closed cases are claim-folding outcomes, not core epistemic guarantees, and must not be read as 'DESi got worse' when the restored core reports them differently or not at all.
- Comparable metrics: branch/critical preservation (core: 1.0; P31/P32 tracked claim branches, a different object). Replay stability, core identity, governance independence, content/method integrity have **no P31/P32 counterpart** — they were never measured there.

## D) Did the benchmark TEST DESi, or CHANGE it?

- It TESTED DESi. 100 tasks ran through the read-only adapter; 10 steering attempts were all refused (10/10 rejected), and the named core areas are 1.0 (byte-identical) vs the canonical base. No core state was mutated.

## E) Were core invariants violated?

- No. replay_stability=1.0, core_identity=1.0 (byte-identical), governance_independence=1.0, mutation_rejection=10/10. The boundary held by construction: `make_task` pins the forbidden set and the adapter refuses steering.

## F) Which periphery stays useful

- `benchmark_api` (boundary-enforced task/result contract), `benchmark_ports` (thin facade: input/output ports, runner, comparison, extractor interface), `benchmark_api_search` / `benchmark_api_drift` adapters, and the external-benchmark dataset loaders. These run ON DESi and are kept.

## G) What to do with the P20–P33 components

- **Discard from the core:** the SPL/meaning-space, typed-governance, folding/DBA, region-alignment, and epistemic-flow layers as *ontology* — they were never core and are not in this restored base.
- **Keep, only as optional adapters/sensors:** a question-grounded extractor and a read-only comparison utility may implement `benchmark_ports.ExtractorPort` / use `compare_results` as benchmark periphery, producing claim *projections* — never the epistemic state space.
- **Isolate as reference experiments:** the P31/P32 reports remain useful as documented warnings (claim-centric governance without a stable ontology drifts toward semantic arbitrariness); they are not part of the core.

## Honesty / limits

- DESi-core metrics only; no truthfulness score. The search-compression metrics come from DESi's deterministic synthetic search space (per the adapter's own stated limitation), not a live planner trace — so they are intrinsic and uniform across tasks by design.
- The 100-task input is the TruthfulQA set reused as benchmark periphery; the P31/P32 numbers are quoted from their committed reports for comparison, not re-executed here.
- No core code changed; no API calls; outputs secret-scanned.
