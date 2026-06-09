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
| `tool_registry.py` | pluggable deterministic tools (ships a `calculator`) |
| `policy.py` | deterministic decision: tool → local → API, by privacy/accuracy/cost |
| `engine.py` | classify → decide → execute → audit |
| `audit.py` | replay-stable SHA-256 over (query + constraints + decision) |
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

This is v0.1: a deliberately small, honest seam. The tool catalogue and the
routing table are meant to grow by measurement, not assertion.
