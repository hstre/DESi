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

Three scripts form an end-to-end loop:

- `desi_gaia_adapter.py` — `solve_gaia_task(task)` connects to the **real** DESi
  runtime and returns `{model_answer, reasoning_trace, desi_metadata}`.
- `solve_gaia.py` — loads GAIA, calls the adapter per task, writes the
  submission JSONL.
- `evaluate_validation.py` — scores the JSONL by exact match.

Run it (default `2023_all` / `validation`, 5 tasks):

```bash
export HF_TOKEN=hf_xxx
python benchmarks/gaia/solve_gaia.py                 # writes outputs/submission.validation.sample.jsonl
python benchmarks/gaia/solve_gaia.py --limit 3 --download-attachments
python benchmarks/gaia/evaluate_validation.py        # exact-match, overall + per level
```

`solve_gaia.py` always degrades gracefully: if the adapter module cannot be
imported it uses a local fallback (`solver: "solve_gaia_local_fallback"`); the
adapter itself returns `solver: "desi_adapter_fallback"` when DESi cannot
produce an answer. Each submission line looks like:

```jsonl
{"task_id": "...", "model_answer": "...", "reasoning_trace": "...", "desi_metadata": {"config": "2023_all", "split": "validation", "level": "2", "has_attachment": false, "file_name": "", "timestamp_utc": "...", "solver": "desi_adapter_fallback", "desi_version_or_commit": "0.1.0", "governance_enabled": true, "replay_enabled": true, "claim_tracking_enabled": true, "attachment_seen": false, "replay_signature": "<sha256>", "error": "no answer-generation backend configured: ..."}}
```

## Stub vs DESi adapter

| | old stub (`solve_task`) | DESi adapter (`solve_gaia_task`) |
| --- | --- | --- |
| DESi import | none | real `desi` (repo `src/` auto-added to path) |
| Governance | none | `desi.core.governance_core.governance_intact()` |
| Replay | none | real `desi.core.replay_kernel.replay_hash` signature per task |
| Claims | none | `desi.self_audit.claim.make_claim_id` |
| `model_answer` | `""` (placeholder) | `""` (no answer backend yet — see below) |
| `desi_metadata.solver` | `"stub"` | `"desi_adapter_fallback"` |

The adapter is a **real connection** to DESi's governance core, replay kernel,
and claim tracking (all pure-stdlib — no network, no API keys). It does **not**
fabricate answers, so exact-match accuracy is still 0% until a real solver is
wired.

## What is connected vs. still missing

**Connected now** (verified at runtime, no secrets): DESi version, governance
integrity check, a deterministic replay signature per task, and claim-id
construction. These populate the `*_enabled` flags and `replay_signature`.

**Still missing — the next technical blocker:** DESi is a governance/audit layer
that classifies and audits LLM *reasoning trajectories*; it does not itself
generate answers. To produce a real `model_answer` we need an LLM
answer-generation step whose trajectory DESi then governs. Concretely:

1. Wire an LLM backend the repo already ships
   (`desi.spl_adapter.deepseek_client.DeepSeekClient` → `DEEPSEEK_API_KEY`, or
   `desi.live_llm_validation.openrouter_client.chat_completion` →
   `OPENROUTER_API_KEY`) to answer `task["Question"]` (+ attachments).
2. Build a `desi.models.Trajectory` from that reasoning and run the full
   governance loop `desi.runner.run_desi` (needs the `pydantic` dependency,
   installed via `pip install desi-governance`).
3. Put the resulting governance verdict (hallucination visibility, replay hash)
   into `desi_metadata` next to the produced `model_answer`.

Until step 1 is done, the adapter stays in `desi_adapter_fallback` mode by
design.
