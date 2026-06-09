# DESi Router (v0.1) — local, tool-and-model routing with a Reviewer Port

A small, mostly-local router built on DESi's discipline: for each query it
decides **tool vs. local model vs. API model**, executes, and shows the decision
and a replay-stable audit in a graphical **Reviewer Port**. Tools run offline and
deterministically; a model is called only if you configure and reach one.

## Run

```bash
# 1. configure providers (local and/or API). Both are OpenAI-compatible.
cp desi/config.example.json desi/config.json   # then edit base_url / models / keys

# 2. start the Reviewer Port (stdlib only, no extra deps)
python -m desi.reviewer_port            # -> http://localhost:8765
#   options: --port 8765  --config desi/config.json
```

Open `http://localhost:8765`, type a query, pick **privacy** (prefer-local /
local-only / any), an accuracy target and a cost budget. You'll see the routed
target, the rationale, the answer, and the audit hash.

- **Local LLMs** (Ollama / llama.cpp / LM Studio / vLLM): set `base_url` to the
  local OpenAI-compatible endpoint (e.g. `http://localhost:11434/v1`), `locality:"local"`.
- **API LLMs** (OpenRouter / DeepSeek / OpenAI): set `base_url` + `api_key_env`
  (the name of an env var holding the key — never the key itself), `locality:"api"`.

Privacy is a first-class routing axis: `local_only` never leaves your network;
`prefer_local` keeps it local when a local model clears the accuracy bar.

## Components

| File | Role |
|---|---|
| `providers.py` | provider registry + one OpenAI-compatible adapter for local **and** API |
| `tool_registry.py` | pluggable deterministic tools: `calculator`, `date_math`, `unit_conversion`, and (with a corpus) `keyword_retrieval` |
| `routing_table.py` | reads **measured** capability scores from `routing_table.json` |
| `policy.py` | deterministic decision: tool → local → API, by privacy/accuracy/cost |
| `engine.py` | classify → check prior (content/method) → reuse or execute → audit → ledger |
| `dedup.py` | content hash (normalized query) + method signature for prior-work lookup |
| `audit.py` | replay-stable SHA-256 over (query + constraints + decision) |
| `ledger.py` | **local Layer 9**: shared, append-only, hash-chained SQLite store |
| `reviewer_port.py` | local web UI (`python -m desi.reviewer_port`) |

## What is verified vs. what runs on your machine

- **Verified (tests + offline HTTP):** config loading, task classification, the
  tool/local/API policy incl. the privacy axis, the engine's **tool path**
  end-to-end (a math query returns the computed answer through the web server,
  fully offline), and audit determinism. See `tests/router_app/`.
- **Runs on your machine, not in CI:** the **model path** (live calls to a local
  or API LLM). It needs a reachable endpoint and, for API providers, a key. The
  routing *decision* and *audit* are produced and reproducible either way; only
  the model's text answer is outside the deterministic boundary.

## Local Layer 9 — one shared ledger across instances

Every routed query is appended to a shared SQLite ledger (`ledger.py`): the local,
running form of the Layer 9 idea. Multiple DESi instances on the machine (or a
shared path) write to the **same file** — point them at it with `--ledger` or the
`DESI_LEDGER` env var. Each row is **append-only** and **hash-chained** to its
predecessor, so any later edit to any past row breaks `verify_chain()`
(Alexandria-style tamper evidence). Concurrency across instances is handled by
SQLite WAL + a serialized IMMEDIATE write.

Inspect it:

```bash
python -m desi.ledger desi/desi_ledger.db --stats --verify --tail 20
```

The Reviewer Port shows the live shared history (count, contributing instances,
chain status) and exposes it at `GET /api/ledger`. Scope: this is the *local*
substrate — one shared file — not the federated cross-institutional Layer 9 of
the working paper. Queries/answers are stored locally; treat the file accordingly.

## Prior-work reuse — don't recompute what the ledger already has

Before working, each instance asks the shared ledger two questions (`dedup.py`):

- **content** — has this exact task been done? Keyed by a light normalization of
  the query (lowercase, collapsed whitespace, trailing punctuation removed;
  operators preserved so `2+2` ≠ `2*2`). A matching **deterministic tool** answer
  is reused exactly (`answer_source: reused:tool#<seq>`) — no recomputation, even
  if a *different* instance produced it. A model answer is reported as a match but
  not auto-reused (it could be stale).
- **method** — has this approach (`task_class | kind | target`) been used before?
  Reported even when the content is new.

Reuse obeys SPL's **S7 invariant** (content ≠ method): identity is `(content,
method_class)` where `method_class` is the closed set `{deterministic, stochastic}`
(a tool is deterministic; a model is stochastic). Results are **never reused or
merged across that boundary** — a stochastic request never serves a deterministic
cached answer, and the same content produced by a different method class is kept
distinct (flagged `content_other_method`). Only deterministic results are reused.

Every result carries a `prior` block (`content_seen`, `method_class`,
`content_other_method`, `method_seen`, `reused`, which instance/seq it came from);
the Reviewer Port shows it per query. This is exact-match reuse, not semantic
similarity — honest and deterministic by design.

## Scores: measured, not asserted

Model capability per task class comes from the **measured** `routing_table.json`
(17 models × 3 task classes) whenever a configured model id exactly matches a
table entry — surfaced as `score_source: "measured"`. A config `task_scores`
hint is used only as a fallback (`config_hint`), and an unmatched local model is
`unmeasured`. A locally-named model never inherits a measured score from a
differently-named API model — that would be a dishonest claim about a different
deployment.

## Tools: deterministic and safe

`calculator`, `date_math` (ISO-date differences/offsets) and `unit_conversion`
(length/mass/temperature) run offline and are exact. `keyword_retrieval` is a
read-only, deterministic search over a local corpus folder, registered only when
you pass `corpus_dir`. **Arbitrary code execution is deliberately not shipped:**
a real code-exec tool needs a sandbox, and an unsandboxed evaluator would be a
security footgun — the registry slot is left open for a sandboxed executor.

This is v0.1: a deliberately small, honest seam. The tool catalogue and the
routing table are meant to grow by measurement, not assertion.
