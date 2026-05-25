# DESi architecture gap analysis: prototype vs. benchmark branch

- **Old branch:** `claude/init-desi-prototype-2QjHF` (HEAD `ce215fa`)
- **Current branch:** `claude/desi-intervention-summary` (the TruthfulQA/GAIA stand)
- **Scope:** `src/desi/{live_llm_validation_granite,_deepseek,_routing}`, `memory/`,
  `self_audit/`, `artifacts/{epistemic_graph,live_llm_validation}`.

## TL;DR — nothing is lost, almost nothing is wired

`git diff origin/claude/init-desi-prototype-2QjHF HEAD -- src/desi` is **empty**:
the entire prototype `src/desi` is **byte-identical** on the current branch. The
benchmark branch only *added* `benchmarks/` (GAIA + static_eval) and a CI tweak —
it did not delete or change a single line of the epistemic machinery.

The real gap is **wiring**, not loss. The benchmark/TruthfulQA pipeline uses DESi
as a thin *metadata stamp* and ignores the rich prototype layers. It imports only:

```
desi.core.governance_core.governance_intact     # boolean integrity check
desi.core.replay_kernel.replay_hash             # per-answer signature
desi.self_audit.claim.make_claim_id             # just the id hash helper
desi.runner.run_desi (+ models.Trajectory)      # run over a 1-step synthetic trajectory
desi.live_llm_validation.openrouter_client      # the network boundary
desi.live_llm_validation.model_registry         # model id
desi.spl_adapter.deepseek_client.DeepSeekClient # a second deepseek client
```

It does **not** touch `live_llm_validation_granite`, `live_llm_validation_deepseek`,
`live_llm_validation_routing`, `self_audit.extractor/replayer/contradictions`, or
any of `memory/` (claim graph, store, recorder, hook).

## What already existed in the prototype

| module | role | status in benchmark pipeline |
| --- | --- | --- |
| `live_llm_validation_granite/` | Granite on 6 **structured** tasks (classification, extraction, JSON-schema, evidence-mapping); `schema_compliance.is_compliant/is_hallucinated` (closed-vocab) | **not wired** |
| `live_llm_validation_deepseek/` | DeepSeek-V4 on 5 **semantic** tasks; `audit_semantic_checks.rubric_score/gap_preserved/ungrounded_token_count` (visible-hallucination) | **not wired** |
| `live_llm_validation_routing/` | complexity-based route (LOW→Granite, HIGH→DeepSeek), `cost_optimizer.routing_cost_reduction`, `escalation_logic.should_escalate`, `governance_router.quality_preservation` | **not wired** |
| `live_llm_validation/` | OpenRouter network boundary + `response_capture` (capture→hash→replay) + `model_registry` | only `chat_completion`/`model_for_role` reused |
| `self_audit/` | `extractor.extract_claims_from_text` (closed kinds HASH/NUMERIC/COUNT/PHASE), `replayer.replay_claims` (verdicts VERIFIED/HASH_MISMATCH/…), contradictions, drift | only `make_claim_id` reused |
| `memory/` | `Claim` (rich lifecycle), `Relation` (6 types), `MemoryStore` (InMemory + Neo4j), `MemoryRecorder`, `MemoryHook` (write-only, replay-safe) | **not wired** |
| `artifacts/epistemic_graph/` | v24 claim graph: 11 node + 9 edge types (Claims, Provenance, Conflicts, Governance, Replay) — read-only, deterministic, offline DryRunClient | n/a (artifacts) |

## Direct answers

- **Which core ideas already existed?** All of the original DESi vision:
  a typed **Claim with a full lifecycle** (`memory/claim.py`:
  PROPOSED→CONFIRMED/REJECTED/MERGED/SPLIT, plus logical/tool/frame states), a
  **claim relation graph** (SUPPORTS/CONTRADICTS/REFINES/DERIVES_FROM/MERGED_INTO/
  SPLIT_FROM), a **claim memory** (`MemoryStore` InMemory + Neo4j, `MemoryRecorder`,
  replay-safe `MemoryHook`), **Granite structured + DeepSeek semantic** runners,
  **complexity routing**, and **self-audit** claim extraction + replay verification.

- **Granite → claim extraction?** *Partly.* Granite produces and scores
  **structured** output (schema compliance, closed-vocab hallucination), but that
  output is **never parsed into `Claim`/`ExplicitClaim` objects** — there is no
  Granite-output→claim bridge.

- **DeepSeek → semantic solver?** *Conceptually yes,* but it is a **capture/replay**
  evaluation over **5 fixed fixture tasks**, scored for rubric/gap/ungrounded
  tokens — not a general solver callable on arbitrary questions, and its output is
  not turned into claims or memory.

- **Claim graph / lifecycle / memory?** *Yes — the richest part of the prototype.*
  `memory/` has the full claim model, lifecycle, relations, store (incl. Neo4j),
  recorder and hook; the v24 epistemic graph artifacts back it. **But** it is fed
  by DESi's *internal trajectory operators* via the optional hook, **not by LLM
  answers**, and it is unused in the benchmark pipeline.

- **Routing Granite↔DeepSeek?** *Yes,* but **static**: tasks carry a fixed
  COMPLEXITY_LOW/HIGH label (LOW→Granite, HIGH→DeepSeek). No dynamic per-query
  routing from live confidence/cost.

- **What is lost or not wired in the benchmark branch?** Nothing lost. **Not
  wired:** granite/deepseek/routing runners, `self_audit` extraction/replay/
  contradictions, and the entire `memory/` claim graph + recorder + hook. The
  benchmark stamps `replay_hash` + `governance_intact` + a claim id and runs
  `run_desi` on a **trivial 1-step synthetic trajectory** (no real trajectory, no
  memory hook, no claim extraction).

- **What new TruthfulQA/GAIA work is still useful?** A lot, and it is genuinely
  new relative to the prototype:
  - **Real, non-fixture LLM evaluation** at scale (50-task TruthfulQA, 10-task
    GAIA) over live OpenRouter — the prototype only ever ran 6 Granite + 5 DeepSeek
    + 11 routing **fixtures**.
  - A reusable **backend layer** (`benchmarks/gaia/desi_gaia_adapter.py`,
    `hf_inference_backend.py`): hf/openrouter/deepseek selection, model resolution
    trace (requested/resolved/provider_returned), `finish_reason` + `usage` capture.
  - The **first DESi action that changes output**: `desi_intervention` converts a
    blocked answer to `UNKNOWN` (hallucination-suspect 4→0 / 8→0 measured).
  - Honest **methodology**: within-file raw→final (no provider-routing noise),
    explicit "heuristic, not truth detection" framing, scoring/report tooling.

## Honest caveats (both sides are incomplete)

- **The prototype never had an end-to-end pipeline either.** Granite/DeepSeek are
  capture/replay phases; self-audit operates on the repo's own markdown (closed
  kinds), not LLM answers; the claim memory is fed by internal trajectories. There
  is **no** existing "solve a question → extract claims → store in the claim graph
  → govern" path. The pieces exist but were never connected into a live loop.
- **The benchmark work is real but thin on DESi.** It proves real-data evaluation
  and a working intervention, but uses DESi as a stamp + an ad-hoc heuristic,
  bypassing the claim lifecycle/graph that *is* the original idea.
- **Both rely on small samples / heuristics**; neither is a general truth check.

## Conclusion

The prototype branch is **closer to the original DESi idea** (typed claims, claim
graph/memory, lifecycle, Granite/DeepSeek/routing, self-audit) — but as an
*unconnected* set of replay-governed phases over fixtures. The benchmark branch is
**closer to real-world evaluation** (live data, a real intervention) — but bypasses
the epistemic machinery. Reintegration means joining the two: feed the new
real-data answers through the existing claim lifecycle + memory + governance. See
`desi_reintegration_plan.md`.
