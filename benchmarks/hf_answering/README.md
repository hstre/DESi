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

## Architectural invariant: `DISSENT_IS_NEVER_AUTHORITY = true`

The wild-brother / dissent layer (challenger, auditor) is **never** a decision
authority. Its outputs are **untrusted raw dissent signals** and must pass the
DESi governance gate (`dissent_governance.filter_dissent`) before any solver or
recheck sees them. Mandatory pipeline:

1. primary solver produces a first verdict;
2. wild brother produces dissent / evidence-gaps;
3. **DESi filters** the dissent — claim-relevant? evidence-based? concrete? not
   generic skepticism? — and **assigns the weight itself** (the wild brother's
   self-claimed strength is ignored), never forcing NOT_ENOUGH_INFO and stripping
   any verdict the dissent asserts;
4. only the governed signal enters the recheck (as a weighted audit branch);
5. the solver may accept or reject it;
6. DESi logs accepted / rejected / pruned-generic / uncertainty-preserved /
   uncertainty-over-amplified / authority-violation attempts.

Forbidden: wild brother → solver directly; → final decision; → automatic NEI
conversion; wild brother as authority; ungoverned dissent in the recheck. The
solver boundary enforces this: `solve_with_dissent` / `solve_recheck` call
`require_governed(...)` and raise `DissentAuthorityViolation` on any dissent not
stamped by the gate (regression-tested in `tests/hf_answering/test_dissent_governance.py`).
The wild brother stays an epistemic disruptor; DESi stays governance.

## Rules

- No benchmark optimization, no prompt-tuning loops, no hidden retries, no answer
  repair heuristics. One deterministic run.
- No core changes, no ontology, no P20–P33 claim-centric redesign.
- Tokens in-process only; never committed; outputs secret-scanned.
- Targeted tests only (`tests/hf_answering`, `tests/benchmark_ports`); no full
  regression unless a protected core file changes.
