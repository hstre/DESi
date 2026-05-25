# GAIA benchmark for DESi

A first integration of the [GAIA benchmark](https://huggingface.co/datasets/gaia-benchmark/GAIA)
(`gaia-benchmark/GAIA`) as an external validation harness for DESi.

## What GAIA measures

GAIA (*General AI Assistants*) is a benchmark of 450+ real-world questions, each
with a single **unambiguous** answer, designed to evaluate tool-augmented
assistants rather than raw text generation. Solving a task typically requires
multi-step reasoning, web search, and reading attachments (spreadsheets, PDFs,
images, audio). Questions are graded into three difficulty levels:

- **Level 1** — solvable by a strong LLM with light tooling.
- **Level 2** — multiple tools / several reasoning steps.
- **Level 3** — long autonomous tool-use chains; a sharp capability jump.

Each level has a public **validation** split (answers + annotator metadata
included) and a **test** split (answers withheld; scored only via the
[leaderboard](https://huggingface.co/spaces/gaia-benchmark/leaderboard)).
Scoring is exact match after light normalization, so the metric is binary per
task and unambiguous — no LLM-as-judge.

## Why GAIA is relevant for DESi

DESi is a deterministic, replay-governed *epistemic governance* layer that sits
around LLM inference: it audits where claims originate, whether they are
supported, whether they drift, and whether a run is bit-exactly reproducible.
GAIA is a good external probe for that layer because:

- **Unambiguous ground truth.** Binary exact-match scoring means a governance
  decision (e.g. blocking a hallucinated answer) can be tied to a verifiable
  outcome rather than a subjective rating.
- **Tool-augmented, multi-step tasks.** GAIA exercises exactly the agentic
  reasoning paths DESi is meant to govern (search, file reading, premature
  closure, authority drift).
- **Hallucination visibility, not elimination.** GAIA's verifiable answers let
  us measure how often DESi makes a wrong/unsupported answer *visible* before
  it is emitted.
- **Replay stability.** The validation split is fixed, so a DESi run over GAIA
  should be reproducible across repeats — a concrete external check of DESi's
  replay-stability invariant.

This directory is the loading/preview layer only; wiring GAIA tasks through a
DESi-governed solver is a later step (see below).

## How to load the dataset

GAIA is **gated**. One-time setup:

1. Sign in to Hugging Face and accept the terms at
   <https://huggingface.co/datasets/gaia-benchmark/GAIA>.
2. Create a token and export it (never commit it):

   ```bash
   export HF_TOKEN=hf_xxx
   ```

3. Install dependencies and run the preview script:

   ```bash
   pip install datasets huggingface_hub
   python benchmarks/gaia/load_gaia.py                 # first 10 validation tasks
   python benchmarks/gaia/load_gaia.py --config 2023_level1 --limit 5
   python benchmarks/gaia/load_gaia.py --download-attachments
   ```

The script reads the token **only** from the `HF_TOKEN` (or
`HUGGINGFACE_HUB_TOKEN`) environment variable and prints `task_id`, `Level`,
`Question`, the attachment (`file_name` + repo `file_path`), and `Final answer`
for each task.

### Data shape

The dataset is Parquet-backed (October 2025 format) with configs `2023_all`,
`2023_level1`, `2023_level2`, `2023_level3` and splits `validation` / `test`.
Columns:

| column | notes |
| --- | --- |
| `task_id` | unique id; used as the submission key |
| `Question` | the prompt |
| `Level` | `1` \| `2` \| `3` |
| `Final answer` | populated for `validation`, withheld for `test` |
| `file_name` | attachment filename, or `""` if none |
| `file_path` | attachment path **relative to the repo root**, e.g. `2023/validation/<id>.pdf` |
| `Annotator Metadata` | struct with the human solving trace/tools |

Attachments are not downloaded by `load_dataset` (only the metadata Parquet is).
Use `--download-attachments` to materialize them via `huggingface_hub`, which
returns the local cached path for each `file_path`.

## Submission format (for later)

The GAIA leaderboard expects a **JSONL** file — one JSON object per line — with
one entry per task in the split being scored:

```jsonl
{"task_id": "c61d22de-5f6c-4958-a7f6-5e9707bd3466", "model_answer": "Saint Petersburg", "reasoning_trace": "1) parsed the question ... 2) searched ... 3) extracted answer"}
{"task_id": "17b5a6a3-bc87-42e8-b0fb-6ab0781ef2cc", "model_answer": "3", "reasoning_trace": "..."}
```

- `task_id` — must match the dataset's `task_id` exactly.
- `model_answer` — the final answer string; it is normalized and compared by
  exact match, so emit the bare value (no prose, units only when the question
  asks for them).
- `reasoning_trace` — optional but recommended; the steps/tool calls taken.

Produce one line per task in the split. For the public score, generate answers
for `2023_all` / `validation`; for the hidden leaderboard score, run over the
`test` split and submit on the leaderboard Space.

## Evaluation pipeline

Five scripts form an end-to-end loop:

- `desi_gaia_adapter.py` — `solve_gaia_task(task, backend=..., model=...,
  prompt_mode=..., skip_attachments=..., dry_run=...)` optionally calls a real
  LLM backend for the answer and always attaches the real DESi
  governance/replay/claim signals.
- `solve_gaia.py` — loads GAIA, calls the adapter per task, writes the JSONL.
- `evaluate_validation.py` — scores the JSONL by exact match.
- `report_validation.py` — summarises a run: attachment split, overall and
  text-only accuracy, per-level accuracy, and the number of UNKNOWN/empty
  answers.
- `analyze_errors.py` — per-task error analysis: classifies each task
  (correct / attachment_skipped / backend_error / reasoning_truncated /
  needs_web_search_or_tools / empty_or_unknown / wrong_answer /
  unknown_failure) and writes a Markdown report.

### Error analysis before scaling up

Run a small batch, then analyse *why* tasks failed before spending money on a
larger run:

```bash
python benchmarks/gaia/analyze_errors.py \
  --submission benchmarks/gaia/outputs/submission.validation.deepseek-v4.textonly.limit10.jsonl
# writes outputs/error_report.<run>.md
```

This step matters because GAIA failures have very different fixes: a
`reasoning_truncated` task just needs a bigger token budget, a
`needs_web_search_or_tools` task needs an actual tool/search loop (not a bigger
model), and `attachment_skipped` needs a file reader. Scaling to the full split
before knowing the failure mix would burn tokens without telling you what to
build next.

### Model strategy

DESi is the **governance / conductor layer**, not the base model. For
DESi-GAIA the intended base models are:

- **IBM Granite** (via Hugging Face Inference) — the open, reproducible
  **baseline**. Set `HF_INFERENCE_MODEL` to a Granite instruct model, e.g.
  `ibm-granite/granite-3.3-8b-instruct`.
- **DeepSeek V4** (via OpenRouter) — the strong **reasoning solver**, model id
  `deepseek/deepseek-v4-pro`.

`Qwen/Qwen2.5-7B-Instruct` and `meta-llama/Llama-3.1-8B-Instruct` were only
**technical smoke tests** to prove the wiring; they are not the DESi-GAIA
strategy. There is **no hard-coded default model** — `auto` never silently
picks one. Granite availability via HF Inference depends on the providers
enabled for your token; if a specific Granite id is "not supported by any
provider", pick another current Granite instruct id (see
`RECOMMENDED_HF_MODELS` in `hf_inference_backend.py`).

### Backends

Three real backends are supported, plus a DESi-only fallback. **Hugging Face
Inference (Granite) is the preferred path** — the same `HF_TOKEN` already used to
load the dataset also drives inference, so no second provider account is needed.

| variable | purpose |
| --- | --- |
| `HF_TOKEN` / `HUGGINGFACE_HUB_TOKEN` | required — gated GAIA access **and** the `hf` backend token |
| `HF_INFERENCE_MODEL` | model id for the `hf` backend, must be chat/instruct capable (recommended: `ibm-granite/granite-3.3-8b-instruct`) |
| `OPENROUTER_API_KEY` | enables the `openrouter` backend (DeepSeek V4) |
| `DEEPSEEK_API_KEY` | enables the native `deepseek` backend |
| `OPENROUTER_MODEL` | optional — override the OpenRouter model (default `deepseek/deepseek-v4-pro`) |
| `DEEPSEEK_MODEL` | optional — override the native DeepSeek model (default `deepseek-4-pro`) |

`--backend auto|hf|openrouter|deepseek|none` (default `auto`). The `auto` order
is: **Granite over HF** when `HF_TOKEN` + `HF_INFERENCE_MODEL` are set, then
**DeepSeek V4** over OpenRouter/DeepSeek when an API key is set, then `none`.
`--model <id>` overrides the per-backend model.

Tokens/keys are read **only** from the environment by the backend clients;
nothing is logged or stored in the repo. `run_desi` (the full governance loop)
additionally needs `pydantic` (`pip install desi-governance`); without it the
adapter keeps the lightweight governance/replay/claim signals and sets
`run_desi_integrated: false`.

### Example calls

```bash
# Preferred baseline: IBM Granite over Hugging Face Inference
export HF_TOKEN=...
export HF_INFERENCE_MODEL=ibm-granite/granite-3.3-8b-instruct
python benchmarks/gaia/solve_gaia.py --backend hf --limit 3
python benchmarks/gaia/evaluate_validation.py        # exact-match, overall + per level

# Strong reasoning solver: DeepSeek V4 over OpenRouter
export OPENROUTER_API_KEY=...
python benchmarks/gaia/solve_gaia.py --backend openrouter --model deepseek/deepseek-v4-pro --limit 3

# Wiring check without spending tokens (resolves backend + model, skips the call):
python benchmarks/gaia/solve_gaia.py --backend hf --dry-run --limit 3

# DESi-only fallback (no LLM call at all) — always works:
python benchmarks/gaia/solve_gaia.py --backend none --limit 3
```

If a Granite id returns "not supported by any provider", switch to another
current Granite instruct id (e.g. `ibm-granite/granite-3.3-2b-instruct`) or
enable a provider that serves it; the pipeline never hard-codes a model.

The pipeline never aborts: if the adapter module itself cannot be imported,
`solve_gaia.py` emits `solver: "solve_gaia_local_fallback"`.

## Three modes: fallback vs LLM-only vs DESi-governed LLM

`desi_metadata.solver` records which mode produced the line:

| `solver` | when | `model_answer` | DESi signals |
| --- | --- | --- | --- |
| `desi_adapter_fallback` | no usable key, `--backend none`, `--dry-run`, or an LLM error | `""` (never fabricated) | governance / replay / claim attached |
| `llm_only` | LLM answered, but `run_desi` not installed (`pydantic` missing) | LLM output | governance_intact + replay_hash + answer claim id |
| `desi_governed_llm` | LLM answered **and** `run_desi` ran over the task trajectory | LLM output | all of the above **plus** `run_desi_metrics` |

Every line also carries `backend`, `dry_run`, `desi_version_or_commit`,
`governance_enabled`, `replay_enabled`, `claim_tracking_enabled`,
`run_desi_integrated`, `attachment_seen`, `replay_signature`, `answer_claim_id`,
and an `audit` struct (`question`, `model_answer`, `backend`, `replay_hash`,
`answer_claim_id`, `error`).

## Attachments and text-only evaluation

Many GAIA tasks ship an attachment (a spreadsheet, PDF, image, or audio file
named in `file_name`). The adapter flags these with
`desi_metadata.requires_attachment: true`, but **it does not yet read the file
content into the prompt**. Answering such a task from the question text alone
would be a blind guess, which inflates the error in an uninterpretable way and —
worse for DESi — looks like a confident hallucination.

Two mechanisms keep the evaluation honest:

- **`--prompt-mode strict` (default).** The model is told to return only the
  final answer and, crucially, to emit `UNKNOWN` rather than guess when the
  evidence is missing. `report_validation.py` counts these separately so you can
  see refusals instead of mistaking them for wrong answers. Use
  `--prompt-mode minimal` for the older bare-answer behaviour.
- **`--skip-attachments`.** Tasks with an attachment are not sent to the model
  at all; their `model_answer` is left empty and `attachment_status` is
  `skipped`. This lets you measure honest **text-only** accuracy first.

```bash
export HF_TOKEN=...
export HF_INFERENCE_MODEL=<a chat/instruct model>
# Text-only run, attachment tasks skipped, then a per-split report:
python benchmarks/gaia/solve_gaia.py --backend hf --limit 10 --skip-attachments
python benchmarks/gaia/report_validation.py
```

This is deliberately more honest than blind guessing: a wrong-but-confident
answer to an attachment task is indistinguishable from a hallucination, whereas
an empty/`UNKNOWN` answer is an explicit "not attempted / not sure". DESi's whole
purpose is to make epistemic state visible, so the pipeline should not
manufacture answers it has no basis for. The real fix is a file reader (see
below); skipping is the honest interim.

## What is connected vs. still missing

**Connected now:** HF Inference (preferred), OpenRouter and DeepSeek answer
generation (env-keyed), DESi governance integrity, a per-task replay signature,
an answer claim id, and — when `pydantic` is installed — the `run_desi`
governance loop over a minimal task-derived trajectory. A real `hf` run
produces `solver: desi_governed_llm` lines (wiring proven with a smoke-test
model; the committed sample uses a generic instruct model, not the
Granite/DeepSeek V4 strategy).

**Still missing for a submittable GAIA run:**

1. **A token + model in the environment** — without them the adapter stays in
   `desi_adapter_fallback` (empty answers). Set `HF_TOKEN` + `HF_INFERENCE_MODEL`.
2. **Attachments are not yet sent to the model.** Tasks with `file_name` are
   flagged (`attachment_seen`) but the file content is not passed in the prompt,
   so attachment-dependent tasks will be wrong until a reader is added.
3. **The trajectory is a single synthetic step.** `run_desi` runs, but a
   faithful multi-step reasoning trajectory (operators, EN events, claims) would
   make the governance verdict meaningful rather than structural.
4. **Run the full split and submit.** Drop `--limit`, run over `2023_all` /
   `validation` for the public score (and `test` for the leaderboard), then
   upload the JSONL to the GAIA leaderboard Space.
