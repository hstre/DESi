# Static evaluation suite for DESi

Offline, reproducible benchmarks that measure **epistemic** properties — the
things DESi actually governs — rather than agent capability. They complement
GAIA (`../gaia/`), which is a web/tool agent benchmark.

## Why static benchmarks matter more for DESi than agent benchmarks

GAIA measures **agent capability**: can the system search the web, read files,
and chain tools? A bare, DESi-governed LLM with no tools scores near zero on
GAIA (our 10-task run: ~11% text-only, 5/9 tasks needed web/search). That low
score says little about DESi — it mostly reflects the *missing tool layer*, so
DESi's governance value is masked by a capability gap.

DESi is a **governance / conductor layer**: it audits truthfulness, makes
hallucinations visible, keeps runs replay-stable, and watches reasoning
efficiency. Those properties are best measured on benchmarks that are:

- **offline** (no web) → deterministic and reproducible,
- **answer-checkable** without a separate agent stack,
- focused on *what the model asserts*, not *what tools it can drive*.

So a model can be a weak GAIA agent yet still be governed well (honest, stable,
efficient) — and static benchmarks are where that shows up.

## Four different things to measure

| dimension | question | example benchmark |
| --- | --- | --- |
| **Agent capability** | Can it use tools/web to get the answer? | GAIA |
| **Epistemic stability** | Same input → same governed output (replay)? Does it drift over long context? | LongBench, replay signature |
| **Hallucination resistance** | Does it assert known falsehoods, or say UNKNOWN? | TruthfulQA, HaluEval, FEVER |
| **Reasoning efficiency** | Does it answer without burning/looping reasoning tokens? | `--reasoning-cutoff`, GSM8K |

DESi should be judged mainly on the last three. GAIA stays as the agent-capability
track. (Note: `src/desi/reasoning_benchmarks` already runs IFEval-format data,
but it tests whether DESi's governance stays stable on the *format* — it does not
run LLM inference. This suite adds the actual governed inference + scoring.)

## Files

- `benchmark_registry.py` — catalog of candidate benchmarks (name, HF repo, type,
  needs_web, needs_attachments, reproducible, DESi relevance, status). Run it to
  print the table: `python benchmarks/static_eval/benchmark_registry.py`.
- `run_truthfulqa.py` — runs TruthfulQA through the DESi adapter (reused from
  `../gaia/desi_gaia_adapter.py`: backend selection, governance, replay/claim,
  model-resolution + usage metadata) and writes a JSONL.
- `report_truthfulqa.py` — heuristic scoring + summary.

## Running TruthfulQA

```bash
export HF_TOKEN=...                     # dataset is public; token still fine
# DeepSeek V4 (strong reasoning solver) over OpenRouter:
export OPENROUTER_API_KEY=...
python benchmarks/static_eval/run_truthfulqa.py \
  --backend openrouter --model deepseek/deepseek-v4-pro --limit 20 --reasoning-cutoff 1500
# or IBM Granite over HF Inference (open baseline):
export HF_INFERENCE_MODEL=ibm-granite/granite-3.3-8b-instruct
python benchmarks/static_eval/run_truthfulqa.py --backend hf --limit 20
# then summarise:
python benchmarks/static_eval/report_truthfulqa.py
```

The runner reuses every DESi signal from the GAIA work: `solver`,
`governance_enabled`, `replay_signature`, `answer_claim_id`,
`run_desi_integrated`, plus `requested_model` / `resolved_model` /
`provider_returned_model`, `finish_reason` and `usage`.

### Scoring (heuristic) and reasoning efficiency

`report_truthfulqa.py` is **not** the official TruthfulQA GPT-judge. It uses
overlap heuristics against the dataset's own answer lists:

- **truthful** — the answer overlaps a `correct_answers` entry.
- **hallucination-suspect** — the answer overlaps an `incorrect_answers` entry
  (these are exactly the common false beliefs TruthfulQA targets).
- **empty/UNKNOWN** — an honest non-answer (better than a confident falsehood).

`--reasoning-cutoff N` flags a record `reasoning_inefficient` when
`finish_reason == "length"` (truncated) or `reasoning_tokens > N`. On TruthfulQA
reasoning is short (a few hundred tokens), so — unlike GAIA — answers are not
truncated, which makes these clean signals to score DESi on.

## Claim memory (P0): answer filter vs. real DESi claims

`claim_memory_adapter.py` is the first reintegration step (P0 from
`artifacts/architecture/desi_reintegration_plan.md`): it records each benchmark
answer as a **real `desi.memory.Claim`** through the existing `MemoryRecorder` /
`InMemoryStore`, mapping the intervention decision to a `ClaimState` and adding a
`SUPPORTS`/`CONTRADICTS` relation to the task's gold-truth claim.

**Answer filter vs. claim memory — the difference:**

| | answer filter (`desi_intervention`) | claim memory (`claim_memory_adapter`) |
| --- | --- | --- |
| output | a possibly-rewritten answer (`UNKNOWN` if blocked) | a typed `Claim` with provenance + lifecycle state |
| state | a one-off `intervention_decision` string | a `ClaimState` (`CONFIRMED`/`PROPOSED`/`REJECTED`) in a store |
| structure | none | claim nodes + `SUPPORTS`/`CONTRADICTS` edges to gold |
| persistence | per-run JSONL | `InMemoryStore` (graph-ready), exported to JSONL |

Run it on an existing run (no new API cost):

```bash
python benchmarks/static_eval/claim_memory_adapter.py \
  --input benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened.refined.limit50.jsonl \
  --output benchmarks/static_eval/outputs/truthfulqa_claim_memory.limit50.jsonl \
  --report benchmarks/static_eval/outputs/truthfulqa_claim_memory_report.md
# or inline during a fresh run:
python benchmarks/static_eval/run_truthfulqa.py --mode desi_intervened ... --record-claims
```

**Why this is the first step back to the DESi core:** earlier the benchmark used
DESi only as a metadata stamp and the intervention only *filtered answers*. P0
turns each answer into a **governed claim with a lifecycle state and relations**,
recorded through the prototype's own claim/memory machinery — moving from "DESi
edited this answer" to "DESi recorded a claim, its state, and how it relates to
the known truth." It is **not yet** a persistent claim graph: claims live in an
in-process `InMemoryStore` and are not yet exported to the v24 epistemic graph /
Neo4j (the next reintegration step).

### P0 (direct recorder) vs P1 (run_desi memory_hook)

P1 (`claim_memory_adapter.record_claims_via_memory_hook`, run via
`--record-claims-via-hook` or `claim_memory_adapter.py --via-hook`) routes the
claim writes through the **real governance lifecycle** instead of a side-channel:

| | P0 `--record-claims` | P1 `--record-claims-via-hook` |
| --- | --- | --- |
| write path | `MemoryRecorder` called directly | `run_desi(trajectory, memory_hook=MemoryHook(...))` |
| run_desi used? | no | **yes** — Run + OperatorEvents + DeterministicMetrics |
| what the hook writes | — | trajectory focus claims (PROPOSED, content=focus id) + `DERIVES_FROM` |
| answer/gold semantics | direct | recorded by the adapter through the same recorder |

**Honest limitation (not hidden):** the stock `MemoryHook` mirrors the
*trajectory's focus claims*; it does **not** map a benchmark `intervention_decision`
to a `ClaimState`. So P1 genuinely runs `run_desi` + the hook (Run, OperatorEvents,
metrics, DERIVES_FROM, replay-safe), but the CONFIRMED/REJECTED + SUPPORTS/
CONTRADICTS semantics are still recorded by the adapter on top. The comparison
report (`*_claim_memory_hook_report.md`) shows both layers explicitly.

**Why P1 is closer to the DESi core:** claims now enter through the same
`run_desi` governance path the prototype uses (lifecycle hook, run scope, replay
safety, deterministic metrics) rather than a bolt-on recorder call. The next step
is a custom hook that carries the answer→ClaimState mapping inside the lifecycle
itself, and persistence to the v24 epistemic graph.

### P2 (prototype): answer-level claims vs. atomic sub-claims

`freetext_claim_extractor.py` + `claim_decomposition_demo.py` are a small,
**heuristic** prototype that moves from "one answer = one claim" to several
**atomic sub-claims**:

> "Virginia Woolf was born in London in 1882 and became a famous writer."
> → `Virginia Woolf was born in London` · `Virginia Woolf birth year = 1882`
> · `Virginia Woolf became a famous writer`

It uses only sentence splitting, a few connectives (`and`/`because`/`but`/`while`),
subject propagation, and a year heuristic — **no semantic parser, no LLM**. Run:

```bash
python benchmarks/static_eval/freetext_claim_extractor.py        # standalone demo
python benchmarks/static_eval/claim_decomposition_demo.py        # store via the P1 hook path + report
```

Each sub-claim is its own `Claim` (own id, `ClaimState`, provenance) with a
`DERIVES_FROM` edge to the parent answer-claim, plus `because`→`SUPPORTS` /
`but`/`while`→`REFINES` edges. The `self_audit.extractor` is **not** reused: it
is closed-kind (HASH/NUMERIC/COUNT/PHASE) and markdown-specific; this is the
free-text counterpart.

**answer-level vs. atomic — and why atomic matters:**

| | answer-level claim (P0/P1) | atomic sub-claims (P2) |
| --- | --- | --- |
| granularity | whole answer = 1 claim, 1 state | each proposition = its own claim/state |
| conflict detection | only answer vs. gold | sub-claim vs. sub-claim, cross-answer |
| revision | revise the whole answer | revise a single wrong fact, keep the rest |
| confidence propagation | one number per answer | per-fact confidence that can aggregate |
| cross-run consistency | hard (answers vary in wording) | match stable atomic facts across runs |

Atomic claims are the precondition for a real **claim graph**: contradictions,
confidence, and revisions live at the level of individual facts, not whole
answers. This prototype is heuristic and **mis-splits many real sentences** (see
`outputs/freetext_claim_decomposition_report.md` for documented failure modes,
e.g. dates like "August 2, 1776", `because of <noun>` fragments, and unresolved
pronouns); a robust model-assisted extractor is future work.
