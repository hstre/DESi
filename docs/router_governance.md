# Router governance — DESi diagnoses, the router acts

A minimal, deterministic governance layer in `desi_router/governance/`. It consumes DESi/Layer-9
diagnostics, chooses an **epistemic mode**, optionally builds a guarded preprompt, **verifies the
answer after the fact**, and audits the decision — without turning DESi into an enforcement engine.

## At a glance

The boundary is fixed throughout: **DESi diagnoses, the router acts, Layer-9 stays the authority on
state.** The router never mutates persistent state — it only decides whether an answer may *propose* an
update and whether a verifier must pass first.

| Component | File | What it does |
|---|---|---|
| Read-only report | `report.py` | projects a Layer-9 snapshot into a router-facing `DesiReport` (+ heuristic risk scores) |
| Mode selector | `modes.py` | a pure, most-cautious-first `select_mode` over 8 epistemic modes |
| State-integrity producer | `state_integrity.py` | turns structural facts (status / provenance / scope / relevance) into a signal — closing the blind spot, honestly splitting reducible from irreducible |
| Guarded preprompt | `preprompt.py` | short mechanical rules prepended in guarded/recovery |
| Correction packet | `correction_packet.py` | a capped, status-bearing prompt prefix prepended **only at risk** — a cheaper actuator than the preprompt |
| Post-answer verifier | `verifier.py` | deterministic rule checks (runtime gate); critical checks block an update proposal |
| Two-tier commit gate | `two_tier_gate.py` | cheap rule gate everywhere; an expensive **semantic** judge only on a *critical* commit |
| Plausible-wrong-slice checks | `missing_opposition.py` · `provenance.py` · `scope.py` · `supersession.py` · `k_stability.py` | five deterministic detectors of a slice that *looks* clean but omits opposition / is thin-sourced / out-of-scope / silently superseded / fragile under widening |
| Unified slice attack | `slice_attack.py` | one entry point that runs all five vectors as a falsification pass — a slice "survives" only if none fire |
| Candidate channels | `clsp.py` · `ontology_probe/` | non-authoritative *producers* (cross-lingual probe, ontology type/scope probe) that feed candidates into the same gate — never decide |
| Audit | `audit.py` | a tamper-evident record per decision |

**What the evidence says (all honest, often null):** state *selection* is load-bearing but **metadata
governance is not a recall effect** (B ≈ E); the router gates **only the risky** commits (100 % recall
on risky, 0 % over-block on clean, on Joni's real ledger); the rule verifier is a sound *gate* but a
noisy *measure*, so a **semantic judge** is needed for the degeneration metrics; the correction packet
cuts relapse to 0 at ~30 % less overhead with no answer damage; and the one real **blind spot** —
plausible-wrong state with no signal — is shrunk to exactly its irreducible core and made visible, not
papered over. Sections below give the numbers and the benchmark phases (1 fixtures · 2 replay · 3 live
· 3.5 semantic verifier · 4 relapse).

## Why governance is not embedded inside DESi

This mirrors what the codebase already does and what the ablations found:

- The `EpistemicGapSnapshot` is a **read-only projection** of Layer-9 (its own comment: *"Kevin and
  DESi must NOT reach into Layer-9 core structures"*). `BlindSpotProposals` are **proposals**, not
  enforcement. So "diagnose, don't enforce" is already the house rule — this layer extends it.
- The ablations showed: correct state **selection** is load-bearing; wrong/neutral/contradictory
  state is actively toxic; **metadata governance is not established as a direct recall effect**; the
  practical win is token efficiency + long-document robustness. ⇒ DESi should expose **state quality
  and risk signals**; the *router* decides what to do with them.

**Boundary:** the router never mutates persistent state. The authoritative state mutation stays in
**Layer-9's gate**; the router only decides whether an answer may *propose* an update and whether a
verifier must pass first. This deliberately avoids a second, competing governance authority.

## The two corrections vs. a naive spec

1. **The router did not consume any epistemic state before this** (`policy.decide` is purely
   tool/local/API by privacy/accuracy/cost). The eight modes are a **new, orthogonal decision axis**
   that composes alongside `decide`, not a replacement.
2. **Risk scores split in two.** Pre-decision `risk_scores` on the `DesiReport` are **deterministic
   heuristics** computed from the signals (used to pick a mode). The real, measurable checks run
   **after** the answer in the verifier (the counterpart of the ablation's degeneration metrics).
   Fields the snapshot does not track (invalidated/superseded claims, extraction confidence) are
   **supplied by the caller** (Layer-9 status / an extraction step), never fabricated in the adapter.

## Modes

| mode | when | effect |
|---|---|---|
| `normal_mode` | low risk, no state needed | plain prompt; may propose state update |
| `state_slice_mode` | clean usable state, low/moderate risk | slice in prompt; verify if moderate |
| `guarded_mode` | invalidated/superseded touched, open conflict to resolve, or high poisoning risk | guarded preprompt + verifier required; no update unless verifier passes |
| `verifier_mode` | a standalone post-answer check (usually expressed as `validator_required` on another mode) | run post-checks |
| `recovery_mode` | a wrong frame already entered the conversation + high poisoning risk | ask the model to recover from the wrong frame using current state |
| `retrieval_mode` | no usable DESi state, evidence-lookup task | BM25 / embedding / hybrid retrieval (router's existing `keyword_retrieval`, extensible) |
| `anti_delphi_mode` | open conflict the answer would resolve, and a challenger module exists | challenge before stabilising (delegates to Kevin/AleXiona, not reimplemented) |
| `ask_user_mode` | required user-specific state missing/ambiguous | request clarification |

Selection is a **pure function** of the report (`select_mode`), most-cautious-first, no LLM judge.

## DesiReport (router-facing, read-only)

`report.py`. Published schema (`schema_dict()`): `task_id`, `user_id?`, `project_id?`,
`selected_state_summary`, `selected_claim_ids`, `invalidated_claim_ids`, `superseded_claim_ids`,
`open_conflict_ids`, `provenance_refs`, `state_recall_estimate?`, `extraction_confidence?`,
`has_usable_state`, flags (`user_specific_missing`, `wrong_frame_present`, `task_touches_invalidated`,
`answer_requires_conflict_resolution`), `risk_scores` (the six heuristics), `recommended_mode`,
`explanation_for_router`, `audit_hash`. (Claim *texts* are carried internally for the verifier but
excluded from the published id-schema.) `report_from_snapshot()` projects a duck-typed snapshot.

## RouterDecision

`modes.py`: `task_id`, `chosen_mode`, `reason`, `input_sources_used`, `preprompt_policy`
(`none`|`guarded`), `validator_required`, `persistent_state_update_allowed` (= **may propose**;
Layer-9 gate is final), `required_post_checks`, `fallback_mode`, `audit_event_id`.
`update_allowed_after_verifier(decision, verifier_ok)` is the final gate on forwarding an update
proposal.

## Failure modes covered

- **invalid_claim_reuse** — reusing an invalidated/superseded claim as fact (verifier blocks update).
- **conflict_closure_without_evidence** — closing an open conflict with no evidence/open cue.
- **unsupported_status_upgrade** — asserting certainty over a hypothesis/conflict/invalidated item.
- **stale_confident_answer** — confident answer while state is missing or superseded.
- **coherence_without_continuity** — fluent answer that preserves little of the selected state (warns,
  does not block).
- **wrong_state_poisoning** — routed to guarded/recovery before the answer; verified after.

Every decision produces a tamper-evident `GovernanceAudit` (hashes report-hash + decision +
post-check + update-allowed), appendable to the router's existing ledger.

## Limitations

- `risk_scores` are **heuristics**, not calibrated probabilities; thresholds are fixed, not tuned.
- The verifier is **rule-based** (token-overlap + cue words) — a conservative first pass, not a
  semantic judge; it shares the ablation evaluator's paraphrase/negation blindness.
- `invalidated/superseded/extraction_confidence` must be supplied by the caller; the gap snapshot
  does not track them.
- `anti_delphi_mode` and real `retrieval` backends delegate to other subsystems
  (Kevin/AleXiona/`tools/retrieval.py`); this layer only routes to them.
- **Metadata governance is NOT proven as a direct recall effect** (B ≈ E across the ablations). This
  layer governs *behaviour around* the state; it does not claim the typing improves recall.

## How this maps onto the ablation data

Two different kinds of artefact: the **ablation measures** (real models, REAL OpenRouter backend,
empirical rates) while this **governance layer enforces** (deterministic, synthetic fixtures, no model
call). They share one thing — the **same metric vocabulary**. The router verifier re-implements the
exact degeneration metrics the ablation measured, so the empirical findings become operational gates.

### What the ablation found (Phase 5, final long-document run, `REAL` backend, 2 reps)

| Condition | Recall (Sonnet 4.5) | Recall (Granite 4.1-8b) | mean input tokens |
|---|---|---|---|
| A — full context | 0.88 | 0.76 | 18 342 |
| **B — DESi state** | **1.00** | **0.96** | **372** |
| B — auto-constructed | 0.96 | 0.88 | 450 |
| **E — status-stripped (budget-matched)** | 1.00 | 0.94 | 379 |
| R1 — BM25 retrieval | 0.52 | 0.44 | 355 |
| R2n — neural retrieval | 0.08 | 0.10 | 355 |

Findings that held: DESi state is load-bearing (**B ≥ A at ~49× fewer tokens**); **B ≈ E**, so the
metadata typing is *not* the recall driver; retrieval without state collapses.

### Where degeneration was measured (rate over reps)

| metric | B | E | **R2n** | A |
|---|---|---|---|---|
| coherence_without_continuity | 0.00 | 0.00 | **0.80** | 0.00 |
| confidence_while_wrong | 0.00 | 0.00 | **0.60** | 0.00 |
| loop_trap | 0.00 | 0.00 | **0.40** | 0.00 |
| contradiction_persistence | 0.00 | 0.10 | 0.00 | 0.60 (Granite) |

`R2n` — neural retrieval *without* DESi state — is the toxic path: fluent, but it loses the state and
is confidently wrong. This is the case `select_mode` never answers blindly.

### The bridge — same metric, now a gate

The governance tests carry **no recall number**; they assert pass/fail that the *gate fires*. The link
is metric-for-metric:

| ablation measures (empirical rate) | router verifier check (enforces) | governance test |
|---|---|---|
| coherence_without_continuity = 0.80 @R2n | `coherence_without_continuity` (warns) | `test_coherence_without_continuity_warns...` |
| confidence_while_wrong = 0.60 @R2n | `stale_confident_answer` (**blocks**) | `test_stale_confident_answer_with_no_state_blocks` |
| invalid-claim reuse (wrong-slice phases) | `invalid_claim_reuse` (**blocks**) | `test_verifier_catches_invalid_claim_reuse` |
| contradiction_persistence = 0.60 @A | `conflict_closure_without_evidence` (**blocks**) | `test_open_conflict_closed_without_evidence` |
| bad_framing_nonrecovery | → routes to `recovery_mode` | `test_high_poisoning_is_guarded_or_recovery` |

And the routing mirrors the recall table: the `R2n` column (no state → collapse + degeneration) is
exactly the situation where `select_mode` refuses a blind answer — no usable state → `retrieval_mode`,
risky state → `guarded`/`recovery` + a required verifier.

**Net:** the ablation is the *evidence* of where an LLM degenerates without/with bad state; this layer
is the *operational response* — the same metrics as deterministic gates, with the governance tests
proving they fire on those failure modes. It does **not** re-open the metadata-governance claim: B ≈ E stands, and
this layer governs behaviour *around* the state, not the extraction quality.

## The benchmark — policy correctness, not answer quality

`desi_router/governance/benchmark/`. The right question for a router is **not** "was the answer good?"
but **"did it pick the right epistemic mode at the right moment — preventing degeneration without
needlessly blocking everything?"** Phase 1 is deterministic (no LLM): 80 synthetic `DesiReport`
fixtures across eight classes (A clean · B missing-state · C missing-user-state · D invalidated · E
open-conflict · F wrong-frame · G stale/retrieval-toxicity · H over-block-control), each carrying the
expected mode, verifier requirement and update permission.

Seven baselines compete (`no_router`, `always_normal`, `always_retrieval`, `always_state_slice`,
`always_guarded`, `simple_threshold`, `desi_router`). Metrics in three groups: **mode accuracy**;
**gate precision/recall** (verifier-required, update-block, and end-to-end *enforcement* — a known-bad
probe answer must be denied an update); and the **cost of governance** (over-blocking rate, unnecessary
verifier/ask-user/anti-delphi, preprompt token overhead). Run: `python -m desi_router.governance.benchmark.run`.

| baseline | mode_acc | verif_recall | block_recall | enforce | **overblock** |
|---|---|---|---|---|---|
| no_router / always_normal | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 |
| always_state_slice | 0.21 | 0.00 | 0.00 | 0.00 | 0.00 |
| always_retrieval | 0.19 | 1.00 | 1.00 | 1.00 | 0.00 |
| **always_guarded** | 0.25 | 1.00 | 1.00 | 1.00 | **1.00** |
| simple_threshold | 0.71 | 1.00 | 1.00 | 1.00 | 0.25 |
| **desi_router** | 1.00 | 1.00 | 1.00 | 1.00 | **0.00** |

**How to read this honestly:**
- The headline is **not** "desi_router = 1.00 everywhere". The expected labels encode the spec's intent
  and the router was *built* to that intent, so its mode-accuracy is high **by construction** (stated
  plainly in `cases.py`). A perfect score here is not evidence on its own.
- The load-bearing comparisons are the ones that hold the inputs constant: **desi_router vs
  always_guarded** — identical safety (block-recall 1.00) but **over-blocking 0.00 vs 1.00**: selective,
  not paranoid. And **desi_router vs simple_threshold** — both consume the *same* `risk_scores`, yet the
  ordered most-cautious-first policy beats a single 0.5 threshold (1.00 vs 0.71 mode-accuracy, 0.00 vs
  0.25 over-blocking). That delta is *not* circular; it isolates the value of the structured policy.
- A router that is "safe" only by always guarding (always_guarded) pays for it in full on the
  over-blocking column. A router that never verifies (no_router/always_normal) fails every safety gate.

### Phase 2 — replay against the real ablation artefacts

`desi_router/governance/benchmark/replay.py` (deterministic, no LLM; run
`python -m desi_router.governance.benchmark.replay`). It reads the committed result JSONs (Phase 3
Sonnet + GPT-4o, Phase 5 Sonnet + Granite), labels each **(model, condition)** point DEGENERATE or
CLEAN from its *measured* metrics, maps the condition to the epistemic **situation** the router would
see, runs `select_mode`, and checks concordance: **does the router protect ⟺ the ablation measured
degeneration?** 28 points across 3 models.

A plausible-wrong slice (C wrong-slice, G neutral-irrelevant) only degenerates if the model *trusts*
it — and the router can only protect against it if DESi/Layer-9 surfaces a **detectable signal** (low
extraction confidence, low state-recall, or a wrong-frame flag). So the replay runs two passes:

| pass | clean | no-state / retrieval | open-conflict | **plausible-wrong slice** | overall |
|---|---|---|---|---|---|
| **signaled** (Layer-9 flags the bad slice) | 1.00 | 1.00 | 1.00 | **1.00** | **1.00** |
| **unsignaled** (the bad slice looks clean) | 1.00 | 1.00 | 1.00 | **0.00** | 0.86 |

The discordant points in the unsignaled pass are *exactly* `C_wrong_slice` and `G_neutral_irrelevant`
(the router stays in `state_slice`, no protection) — nothing structural slips. **This is the
load-bearing, non-circular Phase-2 result:** structural risks (no usable state → retrieval; an open
conflict) are caught whether or not anything is flagged, but the router's protection against a
*plausible-wrong* slice is **exactly as good as DESi's risk signal, no better**. It quantifies the
dependency the whole design rests on — and is why `extraction_confidence` / `state_recall_estimate`
are caller-supplied inputs the router cannot fabricate.

### Phase 3 — live closed-loop (real models)

`desi_router/governance/benchmark/live_loop.py` (needs an OpenRouter key; **never committed**). Eight
scenarios × two arms × two models (Sonnet 4.5 + Granite 4.1-8b = 32 calls, temperature 0). Both arms
see the *same* facts; `no_router` gets a neutral prompt, `desi_router` gets the governance status
(guarded preprompt) and a post-answer verifier gate. Outcomes are measured with the same verifier the
router uses. Results in `ab_evidence/results/router_live_phase3.json` (metrics + answer-stripped rows;
no key).

| arm | invalid-reuse | critical_rate | **pollution_rate** |
|---|---|---|---|
| no_router | 0.00 | 0.19 | **0.19** |
| desi_router | 0.08 | 0.19 | **0.00** |

**The robust result — the gate prevents state pollution.** `no_router` let **3 polluted updates**
through (it closed open conflicts E1/E2 without evidence); `desi_router`'s gate blocked **all** →
pollution 0.19 → **0.00**. That is the live demonstration of the layer's purpose.

**The honest twist — the rule verifier's *precision* is the bottleneck, not the model or the policy.**
On manual inspection, every `desi_router` "critical" flag in this run is a **verifier false positive on
a correct, cautious answer**: in D2 the governed model correctly picked schema-per-tenant *while
flagging the superseded option* (the token-overlap check misread the explicit rejection as reuse); in
E1 it correctly **refused to close the conflict** and asked for evidence ("I cannot resolve … evidence
for either position is missing") — yet was flagged `conflict_closure_without_evidence`. The live run
found a real negation-blindness in the verifier, which we fixed for the clearest case (a rejection cue
in the overlapping unit no longer counts as reuse; `test_rejecting_an_invalidated_claim_is_not_counted_as_reuse`).
Residual *structural* false positives remain (enumerate-then-reject across units; conflict scope words
in cue-free lines). **Conclusion: the gate and the policy are sound; `critical_rate` is not yet a
trustworthy degeneration signal** — a semantic / NLI verifier (Phase 3.5) is the needed upgrade. Small
N, temperature-0 is not fully deterministic on OpenRouter (E2 flipped between runs) — directional, not
a leaderboard.

### Phase 4 — multi-turn relapse, and Phase 3.5 — the semantic verifier

`live_relapse.py` injects an invalidated claim into the flat context, then runs three turns (ask →
neutral double-check probe → a later related question that tempts the bad claim back) for each arm and
model. Relapse = the invalidated claim is reused in turn 2 or 3. The **rule** verifier reported a high
relapse for both arms (no_router 1.00, desi_router 0.67) — but inspection showed every governed flag
was the model *quarantining* the bad claim (often echoing the guarded preprompt's "INVALIDATED:" list
back), not adopting it. The token-overlap check cannot tell quarantine from relapse — the same
precision bottleneck as Phase 3, now amplified by the preprompt.

So **Phase 3.5** (`semantic_verifier.py` + `semantic_rescore.py`) adds an LLM-as-judge that classifies
how an answer *uses* a claim — **adopts / rejects / absent** — used for measurement only (the runtime
gate stays the deterministic rule verifier; no API in the hot path; parser unit-tested without
network). Re-scoring the relapse turns on Sonnet:

| arm | rule relapse | **semantic relapse** |
|---|---|---|
| no_router | 1.00 | **0.67** |
| desi_router | 1.00 | **0.00** |

Of **10 rule-flagged turns, the judge confirmed only 3 as genuine adoption — 7 were rejection /
quarantine false positives (70%).** Corrected, the real finding emerges: **the persisted guarded
preprompt drives genuine relapse to 0.00, while no_router actually relapses (0.67)** — it adopts the
superseded value in a later turn. This is exactly the ablation's "injected claims persist and relapse"
effect, and the router suppresses it. Caveats: small N (3 scenarios, one answering model); the judge
is itself an LLM (better at negation than token overlap, but not ground truth) — directional, not a
leaderboard.

**Takeaway across Phases 3–4:** the gate prevents polluted persistent updates (Phase 3) and the
persisted guard prevents multi-turn relapse (Phase 4) — but **only the semantic verifier makes the
degeneration metrics trustworthy**; the rule verifier is a fast deterministic gate, not an accurate
measure. That split — deterministic gate at runtime, semantic judge for evaluation — is the design
that holds.

## The state-integrity layer — closing the blind spot the benchmark found

`state_integrity.py` + `benchmark/hard_cases.py`. Phase 2 showed the router's one real blind spot:
it protects against a plausible-wrong slice **only when DESi/Layer-9 signals it**. The honest response
is not a cleverer router — it is a better *signal*. This layer is DESi's diagnosis step **before** the
router acts: it reads structural facts only (Layer-9 invalid/supersede status, provenance, conflict
scope, relevance) and emits `state_integrity ∈ {clean, stale, contradictory, suspicious, irrelevant,
uncertain}` + `state_mismatch_risk`, which map to router inputs. Every check is deterministic — *LLM
for language, rules for logic*; no model decides integrity. It sits where `report.py` sits (a read-only
projection of DESi diagnostics), so "DESi diagnoses, the router acts" and the Layer-9 boundary hold.

**The honest design rule is the whole point:** it never certifies the slice is *correct*. A `clean`
verdict means "no structural red flag fired" (`basis = no_flag`) — absence of evidence, not proof. The
blind spot is **split**, not pretended away:

- **Reducible** — a deterministic signal exists (status / provenance / scope / relevance). Converted to
  a real signal; the router protects.
- **Irreducible** — a slice that matches provenance, is relevant, carries no Layer-9 status and
  contradicts nothing is undetectable here by construction. The only honest move is *calibrated
  caution* when ANY secondary doubt exists (low/unknown confidence, borderline relevance) → `uncertain`
  → guarded; if there is genuinely no signal at all, it is an **acknowledged miss**, not a silent one.

13 hard fixtures encode exactly the cases DESi/router need (multi-supersession, wrong-slice near-miss,
user-overlay, conflict-closure, stale-retrieval with **and** without a status signal, plausible-wrong
fully-matching). Each is tagged `deterministic` or `irreducible`. The closure result:

| share | closure | n |
|---|---|---|
| **deterministic blind spot** | **1.00** | 8 |
| irreducible (closed only via calibrated caution) | 0.33 | 3 |
| clean controls (no over-blocking) | 1.00 | 2 |

Honest misses: `SR3_nosignal`, `PW1_plausible` — a fully plausible, fully matching, high-confidence
wrong slice with no Layer-9 contradiction. **By construction, not oversight.** The layer *shrinks* the
blind spot to exactly the part that is unsolvable without an external authority, and makes that part
visible. (This does not re-open the metadata claim — B ≈ E stands; the layer uses metadata to *route*,
not to claim recall.) Run: `python -m desi_router.governance.benchmark.hard_cases`.

## The two-tier commit gate — cheap everywhere, expensive only where it matters

`two_tier_gate.py`. The deterministic gate prevents pollution but is *conservative*: in guarded mode it
drops **every** update proposal, including correct ones, and Phase 3.5 showed many such blocks are rule
false positives. Running a semantic judge on every answer would be slow and costly; never running it
leaves the over-blocking in place. So:

- **Tier 1 (always, deterministic, free):** the rule verifier + `update_allowed_after_verifier`. The
  runtime gate; never calls a model.
- **Tier 2 (only on a *critical* state-update, only if a judge is wired):** `is_critical_update` is a
  deterministic test (touches invalidated/superseded, or an open conflict the answer resolves). On a
  critical commit the semantic judge adjudicates — it **blocks** a genuine adoption Tier 1 missed and
  **recovers** the correct updates Tier 1 conservatively dropped. Layer-9's gate still decides the
  actual mutation; this only forwards a *proposal*.

Live demo (Sonnet, 3 critical scenarios, `python -m desi_router.governance.benchmark.two_tier_demo`):

| gate | updates forwarded | note |
|---|---|---|
| Tier 1 (guarded) | **0 / 3** | blocks all — incl. 2 correct answers |
| Two-tier | **2 / 3** | recovered 2 correct updates; blocked 1 genuine adoption |

The default runtime path is unchanged and deterministic (no `semantic_fn`, or a non-critical commit →
Tier 1 only). The expensive judge is paid for exactly on the rare, high-stakes commits where the cheap
gate's conservatism is most costly — and never as the authority over Layer-9.

## The correction packet — a low-risk router actuator

`correction_packet.py`. The lowest-risk way to make a guarded/recovery answer *more stable*: a short,
mechanical, status-bearing work-state the router prepends **only at risk**. No hidden-state steering,
no logits, no weights, no rebuild of DESi — just an explicit, auditable, switch-off-able prompt prefix.
`packet_applies(report, recovery_mode=, verifier_failed_once=)` fires on exactly the six risk triggers
(invalidated-claim touched, open-conflict touched, high wrong-frame / stale-confident risk, recovery
mode, a verifier that failed once) — **never on clean cases**. `build_correction_packet(report)` emits
a capped (~100–300 token) packet: *current valid state* / *invalidated-superseded (do not reuse)* /
*open conflict (do not close without evidence)* / a fixed *recovery target*.

Architecture stays clean: **DESi** delivers state/risks → the **router** decides packet yes/no → the
**packet** steers the concrete answer → the **verifier** still decides whether a persistent update is
allowed → **Layer-9** stays the authority on state.

Four-arm live test on the Phase-4 relapse scenarios (Sonnet, semantic judge; small N = 3):

| arm | semantic relapse | polluted | answer damage | overhead |
|---|---|---|---|---|
| A — no_router | 0.33 | 0.33 | 0.00 | 0 |
| B — guarded_preprompt | 0.00 | 0.00 | 0.00 | 549 c |
| **C — correction_packet** | **0.00** | **0.00** | **0.00** | **384 c** |
| D — packet + verifier | 0.00 | 0.00 | 0.00 | 384 c |

**The packet drives relapse to 0 (matching the guarded preprompt) at ~30 % less token overhead and
zero answer damage** — it does not break correct answers. So it is a usable, cheaper actuator. The
experiment also re-confirms the rule verifier's noise: `false_positive_block` was high across *all*
arms (incl. no_router), because the model names a bad claim to reject it and the token-overlap check
misreads that — consistent with Phase 3.5, the semantic judge is what makes the metric trustworthy.
Directional (N = 3, one model). Run:
`python -m desi_router.governance.benchmark.correction_packet_experiment`.

## The plausible-wrong-slice checks — the blind spot, made into five detectors

The one real blind spot (a slice that looks clean but is subtly wrong, with **no** status signal) is
attacked by five deterministic checks (no LLM), each catching a different way a slice can mislead:

| # | Check | File | Fires when |
|---|---|---|---|
| 3 | missing opposition | `missing_opposition.py` | a slice-independent full-graph scan finds contradiction / supersession / open-question the slice omitted |
| 4 | thin provenance | `provenance.py` | the slice's support is one-rooted / all-derived / stale (count-based, not entropy) |
| 6 | scope mismatch | `scope.py` | a claim is valid but tagged to a different project / tenant / region than the task |
| 5 | silent supersession | `supersession.py` | a same-scope **newer** sibling the slice omits — displaced-but-unflagged, no contradiction edge |
| 2 | k-stability | `k_stability.py` | widening the slice escalates the mode or withdraws the update → the verdict was not robust |

`slice_attack.py` (#7) runs all five as one falsification pass and reports which fired; a slice
survives only if **none** do. Each check **degrades to caution**, never blocks, and returns `()` /
`False` when its fact is absent — so a report that supplies no scan/provenance/scope keeps its exact
prior behaviour.

**Adopted with evidence, not on fixtures.** On an adversarial fixture set (PWS) all five drive
`false_clean` 1.0 → 0.0 at `over_caution` 0.0. But adoption is gated on a **real-data shadow** over
Joni's graph (per-claim). The decisive case is `same_scope_newer` (#5): on 1 366 claims with a
*topic*-scope it over-fired at **64.8 %** (held back), but once claims carried a deterministic
**subject key**, a re-measurement on the grown graph (2 486 live claims) put it at **7.2 %** — now
selective, so the hold is evidence-liftable. The others are stable across the regrow: `missing_opposition`
**6.4 %** and `thin_provenance` **2.3 %** fire selectively (adopt); `scope_mismatch` is structurally
dead (**0 %**, no scope tags in the data yet); `k_unstable` is marginal (**0.2 %**). The rule is
literal: *an adopted check must pass a real measurement, not just a fixture* — and #5 shows it cuts both
ways (a fixture-correct check is held until the data justifies it, then adopted when it does).

**The Ontology Probe, measured and NOT adopted (yet).** The same shadow ran the ontology channel on the
real graph: of 283 same-subject collision groups (739 claims), WordNet covered **0** tokens (no corpus
→ a silent no-op, fail-open as designed), and even a labelled demo seed found its 4 covered ambiguous
tokens only in *singleton* keys — **0 of 283 collision groups addressable**. Joni's collisions are
genuine same-subject repeats, not homonymy, so the separate-only rule has no target here. Built and
unit-correct, but honestly not adopted on this data.

## Candidate channels — CLSP and the Ontology Probe (producers, never authorities)

Two channels *produce* candidate signals for the gate; neither decides. Both follow the same shape as
the rest of the layer: an LLM (or corpus) does the open-ended part and emits candidates; a
**deterministic, replay-stable core** classifies and gates them; the router consumes only finished
fields. `Layer 9 decides; these only propose.`

### CLSP — Cross-Lingual Semantic Probe (`clsp.py`)

Re-expressing a text in other languages forces different semantic cuts and can surface weak signal —
or hallucinate (a hedge becomes a causal claim). The rule is fixed: **the author's lead language is
the authority; every cross-lingual projection is a probe.** A claim found only in a probe language
stays a *candidate* until it can be re-anchored in the lead source. The deterministic core classifies
each aligned cluster into six categories (`invariant_core` / `emergent_candidate` /
`probe_only_candidate` / `translation_artifact` / `semantic_loss` / `overamplification_risk`),
detects **over-amplification** (a hedged original projected into a stronger claim — including German
litotes like *"nicht ganz unproblematisch"* via a structural double-negation matcher), and decides
promotability. `to_report_inputs()` bridges promotable candidates into `report_from_snapshot` so they
flow through the **same** gate: probe-only / artefact / loss never become trusted state; a weakly
anchored (emergent) candidate lowers extraction confidence so `select_mode` requires a verifier; an
all-`invariant_core` slice is trusted. Benchmark: `false_candidate_rate 0.0`, `overamp_detection 1.0`,
`anchor_rate 1.0`.

### Ontology Probe (`ontology_probe/`)

An ontology (WordNet, later OpenCyc) is one **measurement channel**, never a truth: it offers
type / sense / hypernym hints about a term. The contract is enforced structurally:

- **`may_gate` is a constant property, not a field** — a hint can never be constructed to authorise a
  decision; a `Sense` confidence is capped to `weak`. A hint is metadata, never evidence.
- **Separate-only / asymmetric:** the one consumer signal, `scope_uncertain`, may only *withhold* a
  `same_scope` / supersession flag (reducing over-fire — the #5 failure above), **never assert**
  sameness or conflict. Absence of knowledge asserts nothing (`type_incompatible` is `False` when a
  term is unknown). So a wrong hint can at worst make the router ask to disambiguate — never wrongly
  confident.
- **Fail-open & offline:** adapters are pluggable; a missing corpus or any error yields an
  `unavailable` hint, never an exception in the gate path. **WordNet** is the reference adapter
  (small, offline); OpenCyc is a later optional channel, not the default. A `StaticOntologyAdapter`
  makes the rules unit-testable without a corpus.

Like the slice checks, it is **not wired into the live gate yet** — adoption is gated on a real-data
coverage shadow (Joni `shadow/ontology_coverage_shadow.py`) that measures the addressable pool
(same-subject-key collision groups) and the ontology's actual coverage of those terms.

## Property-based invariants (`tests/router_governance/test_router_properties.py`)

Example tests pin cases; **Hypothesis** pins the *laws* the router hangs on, across generated reports.
Test-only — the live router stays stdlib-only; Hypothesis never enters runtime code. Seven properties:
the CLSP lead-language rule (un-anchored / over-amplified never promotable), no authoritative drift
(promoted ⇒ lead-anchored; the bridge selects a subset of promotable), determinism (equal reports ⇒
equal decision + audit hash), order-invariance (set-like inputs don't move the mode or risk vector),
monotonic caution / k-stability (adding opposition never de-escalates, never grants a withheld
update), and *no free update* (`may_update` never coexists with a pending verifier; a failing verifier
blocks the proposal).

## Red-teaming the gate for UNDER-blocking — what does a clean-looking slice still miss?

The benchmark proves the gate does not over-block; the converse question is sharper: **is there a
wrong slice that survives all five vectors and is allowed to update?** `benchmark/underblock.py`
enumerates a catalogue of "plausible-wrong-but-passes" families and measures each twice — does it
*survive* (the gate misses it), and is it *caught once its missing signal is fed*. The result is a
clean, honest line:

| family | class | survives | caught once fed |
|---|---|---|---|
| supersession via paraphrase (different salient tokens) | signal-quality upstream | yes | yes |
| laundered provenance (N sources, one origin) | signal-quality upstream | yes | yes |
| out-of-scope claim with no scope tag | data-model gap | yes | yes |
| confident-wrong with no opposition in the graph | irreducible (no signal) | yes | — |

The load-bearing conclusion: **every non-irreducible miss is caught the moment its signal is supplied
— so the gate's coverage is bounded by the signals fed to it, not by the check logic.** Closing these
means a better subject key / origin-aware provenance / scope tags in the claim model, not a logic fix.
The one irreducible floor (a false claim whose contradiction was never extracted) is named, not
papered over — only an external evidence step, not a slice check, can see it.

**Do the tests actually pin the logic?** `benchmark/mutation_probe.py` applies decision-critical source
mutations to `modes.py` one at a time and runs the suite: **9/12 killed**. The three survivors are
*provably equivalent* mutants — the discrete risk lattice never yields `wrong_state_poisoning == 0.7`
nor a `max(risk) == 0.4`, so the `>=` boundaries at `_HIGH`/`_MOD` have slack and there is no
off-by-one to catch. The one real gap it surfaced (an `and`→`or` that would over-block a
present-but-untouched invalidated claim) is now pinned by a regression test.

## Next experiments

- Wire `report_from_snapshot` to a live Layer-9 status feed for `invalidated/superseded` + a real
  `extraction_confidence`.
- Replace the rule-based verifier checks with the audited `ab_evidence` degeneration functions behind
  a stable interface, and calibrate the risk thresholds on labelled cases.
- Integrate the mode decision into `engine.py` so one query yields *both* the tool/local/API decision
  and the epistemic mode, in one audit record.

## Demo & tests

```bash
python -m desi_router.governance.demo      # 5 scenarios: valid / invalidated / wrong-frame / conflict / missing-state
pytest tests/router_governance -q          # 122 tests (modes, verifier, gate, state-integrity, packet,
                                           # slice checks, CLSP, ontology-probe, properties, under-block)
python -m desi_router.governance.benchmark.underblock        # the under-block red-team catalogue
python -m desi_router.governance.benchmark.mutation_probe    # do the tests pin modes.py? (9/12, 3 equiv)

# benchmark + experiments (deterministic ones need no key; live ones need OPENROUTER_API_KEY)
python -m desi_router.governance.benchmark.run                          # Phase 1: fixtures × baselines
python -m desi_router.governance.benchmark.replay                       # Phase 2: replay vs the ablation
python -m desi_router.governance.benchmark.hard_cases                   # state-integrity blind-spot closure
python -m desi_router.governance.benchmark.live_loop                    # Phase 3: live closed-loop  (key)
python -m desi_router.governance.benchmark.semantic_rescore             # Phase 3.5: semantic verifier (key)
python -m desi_router.governance.benchmark.correction_packet_experiment # 4-arm packet test           (key)
```
