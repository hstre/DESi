# Router governance — DESi diagnoses, the router acts

A minimal, deterministic governance layer in `desi_router/governance/`. It consumes DESi/Layer-9
diagnostics, chooses an **epistemic mode**, optionally builds a guarded preprompt, **verifies the
answer after the fact**, and audits the decision — without turning DESi into an enforcement engine.

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
is the *operational response* — the same metrics as deterministic gates, with 26 tests proving they
fire on those failure modes. It does **not** re-open the metadata-governance claim: B ≈ E stands, and
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

Phase 4 (multi-turn relapse / persistence: inject a bad claim, answer, neutral probe, later related
question, check whether the bad claim returns) remains the last scaffolded step.

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
pytest tests/router_governance -q          # 13 tests
```
