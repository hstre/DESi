"""Deterministic router-mode selection from a DesiReport.

Eight epistemic modes form a NEW decision axis that composes ALONGSIDE the existing tool/local/API
``policy.decide`` (privacy/accuracy/cost) — it does not replace it. The selection is a pure function
of the report (no LLM judge), so it is replay-stable and unit-testable.

Two corrections vs. the naive spec, grounded in the real code:
  * ``persistent_state_update_allowed`` means **the answer MAY PROPOSE** a state update — the final,
    authoritative mutation still goes through Layer-9's deterministic gate. The router never mutates
    persistent state itself; it only decides whether to attempt a proposal and whether a verifier
    must pass first (see ``update_allowed_after_verifier``).
  * Verification is a POST-ANSWER gate triggered by ``validator_required`` + ``required_post_checks``;
    ``verifier_mode`` is kept as an explicit constant for callers that run a standalone post-answer
    check, but the selector normally expresses it via ``validator_required`` on another mode.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from desi_router.governance.report import DesiReport

NORMAL = "normal_mode"
STATE_SLICE = "state_slice_mode"
GUARDED = "guarded_mode"
VERIFIER = "verifier_mode"
RECOVERY = "recovery_mode"
RETRIEVAL = "retrieval_mode"
ANTI_DELPHI = "anti_delphi_mode"
ASK_USER = "ask_user_mode"
MODES = (NORMAL, STATE_SLICE, GUARDED, VERIFIER, RECOVERY, RETRIEVAL, ANTI_DELPHI, ASK_USER)

_HIGH = 0.7
_MOD = 0.4


@dataclass
class RouterDecision:
    task_id: str
    chosen_mode: str
    reason: str
    input_sources_used: tuple[str, ...] = ()
    preprompt_policy: str = "none"                 # "none" | "guarded"
    validator_required: bool = False
    persistent_state_update_allowed: bool = False  # = MAY PROPOSE (Layer-9 gate is final authority)
    required_post_checks: tuple[str, ...] = ()
    fallback_mode: str | None = None
    audit_event_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# the post-checks that matter when a given risk is elevated
_CHECKS_FOR = {
    "invalid_claim_reuse": "invalid_claim_reuse",
    "conflict_closure_risk": "conflict_closure_without_evidence",
    "stale_confident_answer": "stale_confident_answer",
    "wrong_state_poisoning": "unsupported_status_upgrade",
    "coherence_without_continuity": "coherence_without_continuity",
}


def _post_checks(report: DesiReport, *, elevated: float = _MOD) -> tuple[str, ...]:
    out = [check for risk, check in _CHECKS_FOR.items() if report.risk_scores.get(risk, 0.0) >= elevated]
    return tuple(dict.fromkeys(out))


def select_mode(report: DesiReport, *, retrieval_available: bool = True,
                anti_delphi_available: bool = False) -> RouterDecision:
    r = report.risk_scores
    checks = _post_checks(report)

    def decision(mode, reason, *, preprompt="none", validate=False, may_update=False,
                 fallback=None, sources=("desi_report",)):
        return RouterDecision(
            task_id=report.task_id, chosen_mode=mode, reason=reason, input_sources_used=sources,
            preprompt_policy=preprompt, validator_required=validate,
            persistent_state_update_allowed=may_update,
            required_post_checks=checks if validate else (), fallback_mode=fallback)

    # --- ordered deterministic rules (most-cautious first) ---------------------------------------
    if report.user_specific_missing:
        return decision(ASK_USER, "required user-specific state is missing/ambiguous; cannot infer "
                        "safely", sources=("desi_report",))
    if not report.has_usable_state and retrieval_available:
        # retrieval is the ablation's toxic path (R2n: coherence-loss/confident-wrong without state),
        # so a retrieval answer always carries a post-answer verifier before it may propose anything.
        return decision(RETRIEVAL, "no usable DESi state; task is evidence lookup -> retrieve "
                        "(verify before trusting retrieved text)", validate=True,
                        sources=("retrieval",))
    if r["wrong_state_poisoning"] >= _HIGH and report.wrong_frame_present:
        return decision(RECOVERY, "wrong frame already in conversation + high poisoning risk -> "
                        "recover from the wrong frame using current valid state", preprompt="guarded",
                        validate=True, fallback=GUARDED)
    if r["wrong_state_poisoning"] >= _HIGH:
        return decision(GUARDED, "high wrong-state-poisoning risk", preprompt="guarded",
                        validate=True, fallback=RECOVERY)
    if (report.invalidated_claim_ids or report.superseded_claim_ids) and report.task_touches_invalidated:
        return decision(GUARDED, "task touches invalidated/superseded claims", preprompt="guarded",
                        validate=True, fallback=VERIFIER)
    if report.open_conflict_ids and report.answer_requires_conflict_resolution:
        if anti_delphi_available:
            return decision(ANTI_DELPHI, "open conflict the answer would resolve; challenge before "
                            "stabilising", preprompt="guarded", validate=True, fallback=GUARDED)
        return decision(GUARDED, "open conflict the answer would resolve (no anti-delphi module) -> "
                        "keep it open", preprompt="guarded", validate=True, fallback=GUARDED)
    if max(r.values()) >= _MOD:
        return decision(STATE_SLICE, "moderate risk; give the slice + verify the answer",
                        validate=True, may_update=False, fallback=GUARDED)
    if report.has_usable_state:
        return decision(STATE_SLICE, "clean usable state, low risk", may_update=True)
    return decision(NORMAL, "no state needed, low risk", may_update=True, sources=())


def update_allowed_after_verifier(decision: RouterDecision, verifier_ok: bool) -> bool:
    """Final 'may this answer PROPOSE a persistent-state update?' — only if the decision allowed a
    proposal AND (no verifier required OR the verifier passed). Layer-9's gate remains the final word
    on the actual mutation; this just decides whether to forward a proposal at all."""
    if not decision.persistent_state_update_allowed:
        return False
    if decision.validator_required and not verifier_ok:
        return False
    return True
