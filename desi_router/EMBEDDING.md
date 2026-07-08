# Embedding the DESi Router — the building-block guide

The DESi router is a self-contained Python package: **stdlib only, zero
dependencies, no imports from the rest of the DESi repository**. You can drop it
into any Python ≥ 3.11 application and get, per query:

1. a **deterministic routing decision** — tool vs. local model vs. API model,
   under an explicit privacy / accuracy / cost policy,
2. **execution** — deterministic tools run offline and exactly; a model is
   called only if you configured one and it is reachable,
3. a **replay-stable audit hash** over (query + constraints + decision), and
4. optionally a **shared, append-only, hash-chained ledger** (the local
   Layer 9) with exact prior-work reuse.

The decision and audit are always produced, network or not. Only a live model
answer sits outside the deterministic boundary — an unreachable model returns
the decision with an `error` field, never a crash.

## 1. Get it (three ways, same import surface)

**a) Vendor the folder** — copy `desi_router/` into your project root (or your
packages dir). It has no dependencies, so this is a legitimate, supported way
to embed it:

```
your-app/
├── your_app/
├── desi_router/        <- copied verbatim from the DESi repo
└── ...
```

**b) Install from the repo subdirectory:**

```bash
pip install "desi-router @ git+https://github.com/hstre/DESi#subdirectory=desi_router"
```

**c) Run from a DESi checkout** — from the repo root, `desi_router` is directly
importable (this is how the Reviewer Port and the tests use it).

Whichever you pick: `import desi_router` and everything below is identical.

## 2. Two lines to a routed answer

```python
from desi_router import DesiRouter

router = DesiRouter()                                # no config: tools only, fully offline
print(router.route("What is 17 * 23?")["answer"])    # -> 391, answer_source: "tool"
```

A `DesiRouter()` without providers still answers everything its deterministic
tools cover (arithmetic, date math, unit conversion — retrieval if you pass
`corpus_dir=`). Nothing leaves the process.

With models:

```python
router = DesiRouter.from_config("config.json")       # see config.example.json
result = router.route(
    "Summarize the drift findings in this abstract: ...",
    privacy="prefer_local",        # "local_only" | "prefer_local" | "any"
    accuracy_target=0.8,           # minimum measured/hinted task score
    cost_budget_usd=0.01,          # hard ceiling per query
)
result["decision"]["target"]       # e.g. "ollama-local/llama3.1:8b"
result["decision"]["rationale"]    # why, in one sentence
result["answer"]                   # None if no model was reachable/allowed
result["error"]                    # honest reason when answer is None
result["audit"]["decision_hash"]   # replay-stable SHA-256
```

Configuration can come from your own settings machinery instead of a file —
same shape as `config.example.json`:

```python
router = DesiRouter({
    "providers": [{
        "name": "ollama-local",
        "base_url": "http://localhost:11434/v1",
        "api_key_env": None,                         # env-var NAME for API providers
        "models": [{"id": "llama3.1:8b", "locality": "local",
                    "cost_per_item_usd": 0.0,
                    "task_scores": {"code_audit": 0.83}}],
    }]
})
```

Local and API providers are the same thing — an OpenAI-compatible
`/v1/chat/completions` endpoint. Ollama / llama.cpp / LM Studio / vLLM locally;
OpenRouter / DeepSeek / OpenAI remotely. API keys are referenced by
**environment-variable name** (`api_key_env`), never stored in config.

### The privacy axis

- `local_only` — the query never leaves your network. If no local model (or
  tool) fits, you get the decision `kind: "none"` with the reason, not a silent
  API fallback.
- `prefer_local` (default) — local wins whenever a local model clears the
  accuracy bar; API only when it doesn't.
- `any` — best score-per-cost regardless of locality.

Deterministic tools always win over any model when they cover the task:
exact, $0, local.

## 3. Decision only — keep execution in your hands

If your application has its own LLM client, queueing, retries or streaming,
embed only the *deterministic decision layer*:

```python
decision = router.decide("Review this diff for injection bugs", privacy="any")
if decision.kind == "model":
    provider, model_id = decision.extras["provider"], decision.extras["model_id"]
    # dispatch through YOUR client, with YOUR retry/streaming logic
elif decision.kind == "tool":
    ...
```

`decide()` is a pure function of (query, constraints, your config, the tool
registry): no network, no disk, fully unit-testable inside your test suite.

## 4. Your own deterministic tools

```python
def lookup_order(query: str) -> str:
    ...                                  # raise on input you cannot parse

router.add_tool("order_lookup", {"retrieval"}, lookup_order)
```

A registered tool covers one or more task classes; when the classifier maps a
query to a class your tool covers, the tool wins over every model. Keep tools
deterministic — a stochastic step belongs behind a model provider, otherwise
the audit and reuse guarantees would lie. (Arbitrary code execution is
deliberately not shipped; bring a sandboxed executor if you need one.)

Task classes are decided by `desi_router.policy.classify` (keyword-based,
overridable per call: `router.route(..., task_class="retrieval")`).

## 5. The shared ledger (local Layer 9) — optional, one argument

```python
router = DesiRouter.from_config("config.json", ledger="~/.your-app/desi_ledger.db")
```

Every routed query is appended to a hash-chained SQLite ledger; edits to any
past row break `verify_chain()`. Several embeddings / instances may point at
the **same file** — they share prior work:

- an identical query answered by a **deterministic tool** before (by any
  instance) is **reused exactly**, not recomputed
  (`answer_source: "reused:tool#<seq>"`);
- a prior **model** answer is *reported* (`prior.content_seen`) but never
  auto-reused — it could be stale, and reuse never crosses the
  deterministic/stochastic boundary (SPL S7).

Without the argument the router touches no disk at all. Inspect a ledger:

```bash
python -m desi_router.ledger path/to/desi_ledger.db --stats --verify --tail 20
```

`DesiRouter` is a context manager; `with DesiRouter(...) as r:` closes a ledger
it opened itself (a `Ledger` instance you pass in stays yours to manage).

## 6. What to rely on (and what not)

- **Deterministic, always:** classification, the routing decision, the audit
  hash, tool execution, ledger chaining, reuse. These are covered by the test
  suite (`tests/router_app/`) and run offline.
- **Live, environment-dependent:** a model's text answer. Requires a reachable
  endpoint (and a key for API providers). Failures are surfaced in
  `result["error"]` with the decision intact.
- **Scores are measured, not asserted:** when a configured model id exactly
  matches the empirical `routing_table.json`, the measured score is used
  (`score_source: "measured"`); your config's `task_scores` are a fallback
  hint; an unknown local model is honestly `unmeasured` — it never inherits a
  differently-named API model's score.

## 7. Going deeper

| You want | Import |
|---|---|
| The one-object facade | `from desi_router import DesiRouter` |
| Raw engine under the facade | `from desi_router import run, Constraints` |
| Provider registry from dict/file | `from desi_router import registry_from_dict, load_config` |
| Tools | `from desi_router import Tool, ToolRegistry, default_registry` |
| Ledger | `from desi_router import Ledger` |
| Benchmark-grounded Pareto router (measured task classes, escalation) | `from desi_router import EpistemicRouter, RouteRequest, DESiPipeline` |
| The local web UI on top of the same engine | `python -m desi_router.reviewer_port` |

The wider context — Reviewer Port, prior-work semantics, calibration — is in
`ROUTER_APP.md` and `CALIBRATION_GUIDE.md` next to this file.
