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
