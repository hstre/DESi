# HF answering benchmark layer (PERIPHERAL)

The semantic-flow constitution is immutable. Benchmark layers are peripheral.
**Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is NOT the
answer generator.**

This layer runs a real external QA benchmark with real model answers and real
scoring, while recording DESi-core invariants alongside. It is pure periphery:
no core import beyond the read-only `desi.benchmark_ports` / `desi.benchmark_api`
boundary, no ontology, no governance changes.

## Architecture (clean separation)

```
HF dataset  ──►  model port  ──►  generated answer  ──►  evaluator (bool acc + confusion)
   │              (external)                                   │
   └──────────────────────────────────────────────────────────┴──►  DESi-core metrics
                                                                      (recorded alongside,
                                                                       core untouched)
```

- **dataset** (`answer_runner.load_boolq`): `google/boolq`, validation split.
- **model port** (`models.py`): an *external* model. `OpenRouterPort` (Granite
  4.1-8b / Claude Haiku 4.5 / GPT-4.1-mini, via `OPENROUTER_API_KEY`),
  `HFInferencePort` (`HF_TOKEN`), or `ConstantBaselinePort` (offline baseline,
  for wiring only). Ports read their token in-process and raise loudly if it is
  missing — they never fabricate an answer.
- **evaluator** (`evaluator.py`): one fixed prompt, exact yes/no parse, exact
  accuracy + confusion matrix. One deterministic pass — no tuning, no retries,
  no repair.
- **DESi-core metrics** (`answer_runner.desi_core_metrics`): replay stability,
  core identity, governance independence, critical-branch preservation, and
  mutation rejection, via the tested `SearchCompressionAdapter`. DESi processes
  none of the model's output; it only shows its own behavior is unchanged.

## Run

```bash
# real Granite run (needs OPENROUTER_API_KEY in the environment, in-process only)
python3 benchmarks/hf_answering/answer_runner.py --model granite --backend openrouter --limit 100

# real Claude / GPT
python3 benchmarks/hf_answering/answer_runner.py --model claude --backend openrouter --limit 100
python3 benchmarks/hf_answering/answer_runner.py --model gpt    --backend openrouter --limit 100

# offline pipeline wiring/smoke (deterministic baseline, no token, NOT a model result)
python3 benchmarks/hf_answering/answer_runner.py --backend baseline --limit 100 --report boolq_wiring_smoke.md
```

Without a token the real run is reported as **BLOCKED** with the exact reason —
no answers are fabricated and the offline baseline is never passed off as a
model result.

## Rules

- No benchmark optimization, no prompt-tuning loops, no hidden retries, no answer
  repair heuristics. One deterministic run.
- No core changes, no ontology, no P20–P33 claim-centric redesign.
- Tokens in-process only; never committed; outputs secret-scanned.
- Targeted tests only (`tests/hf_answering`, `tests/benchmark_ports`); no full
  regression unless a protected core file changes.
