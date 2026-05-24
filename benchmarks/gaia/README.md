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

## Stub evaluation pipeline

`solve_gaia.py` and `evaluate_validation.py` form a minimal end-to-end loop.
**The solver is a stub** — `solve_task()` returns an empty answer. It only
validates the pipeline (load → solve → serialize → evaluate) and is **not** a
real DESi solver yet, so expect 0% accuracy.

Generate a sample submission (default `2023_all` / `validation`, 5 tasks):

```bash
export HF_TOKEN=hf_xxx
python benchmarks/gaia/solve_gaia.py
python benchmarks/gaia/solve_gaia.py --limit 20 --download-attachments
```

This writes `outputs/submission.validation.sample.jsonl`, one line per task:

```jsonl
{"task_id": "...", "model_answer": "...", "reasoning_trace": "...", "desi_metadata": {"solver": "stub", "config": "2023_all", "split": "validation", "level": "2", "has_attachment": false, "file_name": "", "timestamp_utc": "..."}}
```

Then score it against the validation `Final answer`s (simple, case- and
whitespace-insensitive exact match — **not** the official GAIA scorer):

```bash
python benchmarks/gaia/evaluate_validation.py
python benchmarks/gaia/evaluate_validation.py --submission benchmarks/gaia/outputs/submission.validation.sample.jsonl
```

It prints overall and per-level exact-match accuracy.

## Next step: replace the stub with a real DESi solver

Swap the body of `solve_task()` in `solve_gaia.py` for a DESi-governed solver
that routes `task["Question"]` (plus any attachment at `task["file_path"]`)
through DESi and returns the produced `model_answer` and `reasoning_trace`.
Keep the DESi audit trail in `desi_metadata` (e.g. hallucination flags, replay
signature) so accuracy can be reported per level next to DESi's governance
metrics. Then run over the full `validation` split (drop `--limit`) and, for the
hidden leaderboard score, over the `test` split.
