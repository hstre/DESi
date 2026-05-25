# DESi reintegration plan

Goal: connect the **real-data benchmark pipeline** (new: `benchmarks/`) to the
**epistemic machinery** that already exists in `src/desi` (claim lifecycle, claim
graph/memory, governance, Granite/DeepSeek/routing) — so DESi stops being a
metadata stamp and becomes the conductor it was designed to be.

This is a **plan only** — no code is changed here. See
`desi_architecture_gap_analysis.md` for the inventory and evidence.

## Principles (keep DESi's invariants)

1. **Reuse, don't reimplement.** Every target module already exists and is tested.
2. **Replay-safe + deterministic.** Writes go through the existing write-only
   `MemoryRecorder`/`MemoryHook`; identical input → identical `run_desi` output
   (the hook never feeds back into diagnostics).
3. **Governance stays read-only.** The claim memory/graph records *why* a result
   is valid; it must not steer decisions or introduce hidden state.
4. **No secrets, env-only keys** (unchanged).
5. **Default to `InMemoryStore`** (pure-stdlib); Neo4j stays optional.

## Phased plan

### P0 — Answer → Claim in the claim memory (the first patch)

**What:** In the benchmark run loop (TruthfulQA/GAIA), wrap each task in a
`MemoryRecorder` run and record the model answer as a `memory.claim.Claim`, with
the **intervention decision mapped to a `ClaimState`** and a relation to the gold:

- map `accept_supported → CONFIRMED`, `accept_uncertain → PROPOSED`,
  `reject_known_false → REJECTED`, `reject_low_confidence → UNDER_LOGICAL_AUDIT`,
  `abstain* → PROPOSED` (tool/evidence required);
- add a `Relation` (`SUPPORTS`/`CONTRADICTS`) from the answer-claim to a
  gold-answer claim (for TruthfulQA, from the correct/incorrect lists).

**Reuses (all present, dependency-light):** `memory.recorder.MemoryRecorder`
(`start_run`/`record_claim`/`record_relation`/`end_run`), `memory.store.InMemoryStore`,
`memory.claim.Claim` + `ClaimState`, `memory.relations.RelationType`.

**Why first:** highest leverage / lowest risk. It turns the ad-hoc heuristic
intervention into a **governed claim-lifecycle transition recorded in the claim
graph**, directly bridging the new real data to the original idea — without
touching the fixture-bound Granite/DeepSeek runners. Output: a per-run claim
graph (`store.all_claims()` / `relations_for()`) that the v24 export layer can
later render.

**Acceptance:** for a 50-task run, each task yields exactly one answer-claim with
a state matching its `intervention_decision`, plus one gold relation; re-running
the same captured answers produces an identical claim set (replay-stable).

### P1 — Real `run_desi` trajectory + `MemoryHook`

**What:** Replace the current **synthetic 1-step trajectory** with a `Trajectory`
built from the actual solve (question → answer step → intervention verdict step),
and attach `memory.hook.MemoryHook` to `run_desi(trajectory, memory_hook=hook)`
so the claim/relation writes happen through the intended lifecycle path instead of
ad-hoc P0 calls.

**Reuses:** `runner.run_desi(..., memory_hook=)`, `memory.hook.MemoryHook`,
`models.Trajectory/TrajectoryStep`. **Note:** keep `run_desi` output identical
with/without the hook (tested invariant in `tests/test_runner.py`).

### P2 — Claim extraction from free-text answers (new small adapter)

**What:** A minimal `answer → claim` extractor for QA answers. **Do not** reuse
`self_audit.extractor` directly: it is intentionally **closed-kind**
(HASH/NUMERIC/COUNT/PHASE) and tuned to the repo's own markdown, not free text.
Add a thin benchmark-side extractor that emits one (or few) `Claim`(s) per answer
with provenance; optionally classify the answer kind (numeric/entity/boolean).

**Reuses:** `memory.claim.Claim`; mirrors `self_audit.replayer` verdict idea for
the gold comparison. Lower priority than P0/P1.

### P3 — Generalize Granite/DeepSeek + routing to real questions

**What:** Today `granite_runner`/`deepseek_runner` are bound to fixed fixture
tasks (`structured_tasks()`, `semantic_tasks()`) and capture/replay. To use the
**routing** idea (LOW→Granite cheap, HIGH→DeepSeek) on real benchmarks, generalize
the runners to accept an arbitrary prompt and let `routing_engine`/`escalation_logic`
pick the model from a per-question complexity signal.

**Reuses:** `live_llm_validation_routing.{routing_engine,escalation_logic,cost_optimizer,governance_router}`,
`live_llm_validation.openrouter_client.chat_completion`, `model_registry`.
**Effort:** highest (runners are fixture-coupled); do after P0–P1 prove the claim
loop. **Payoff:** real cost-routing on real workloads (the prototype's 53.5%
reduction was over 11 fixtures only).

### P4 — Epistemic-graph export of benchmark runs (optional)

Once answer-claims live in the store (P0), reuse the v24 export layer
(`artifacts/epistemic_graph`, offline DryRunClient) to render the per-run claim
graph read-only. Keep Neo4j optional.

## Non-goals / risks

- **Do not** let the claim memory or graph influence decisions (read-only
  governance); P0–P4 are observational/record + lifecycle, not control feedback.
- **Do not** reintroduce non-determinism: all writes via `MemoryRecorder`; the
  stochastic boundary stays the single LLM call.
- **Do not** overclaim: even fully wired, this is heuristic claim handling on a
  reference set, not general truth detection.

## The single most important next patch

**P0 — record each benchmark answer as a `memory.claim.Claim` via
`MemoryRecorder`, with the intervention decision as its `ClaimState` and a
`SUPPORTS`/`CONTRADICTS` relation to the gold answer.** It reuses already-present,
pure-stdlib, replay-safe modules, needs no change to the fixture-bound runners,
and is the smallest step that reconnects the new real-data evaluation to DESi's
original claim-lifecycle/graph — converting "DESi stamped this answer" into "DESi
recorded a governed claim and its lifecycle decision."
