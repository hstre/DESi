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

## Two layers: dataset-guided intervention vs general epistemic heuristics

DESi's intervention now has two distinct layers, with very different scope:

| | dataset-guided (`reject_known_false`) | general epistemic checks (`general_epistemic_checks.py`) |
| --- | --- | --- |
| needs a reference answer set? | **yes** (TruthfulQA correct/incorrect lists) | **no** — looks only at the answer text + call signals |
| what it catches | answers matching a *known* false answer | surface risk patterns: over-confident phrasing, contradictions, evasions, runaway reasoning |
| action | **blocks** (replaces with `UNKNOWN`) | **flags / downgrades confidence / annotates** — never blocks on its own |
| decisions | `reject_known_false`, `abstain*` | `reject_unsupported_certainty`, `reject_contradictory`, `downgrade_low_evidence`, `accept_low_confidence` (all non-blocking) |

The general checks (`--general-checks`, on by default in `desi_intervened`) add
`epistemic_flags`, `epistemic_risk_score`, `confidence_band`, and
`reasoning_efficiency_score` to `desi_metadata`. UNKNOWN is still only set on
robust known-false evidence or truncation/inefficiency.

### Clear limits

- **Not a general truth check.** The general heuristics are surface-level
  *risk* signals (lexical certainty markers, polarity-pair contradictions,
  hedge phrases, reasoning/answer ratio). They do **not** verify facts and can
  miss real errors and fire on harmless phrasing.
- They are deliberately **non-aggressive**: they reduce confidence and annotate,
  they do not discard answers. Only the dataset-guided layer (with a reference
  set) and truncation/inefficiency abstains actually block.
- On a reasoning model, `reasoning_inefficiency` fires often (the model reasons
  a lot for short answers); treat it as an efficiency signal, not a hallucination
  predictor. See `report_epistemic.py` and the generated report for how the
  flags relate (or fail to relate) to hallucination-suspect labels.
