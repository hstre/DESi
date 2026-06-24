"""Two-tier commit gate — cheap deterministic everywhere, expensive semantic only when it matters.

Phase 3 showed the deterministic rule gate prevents state pollution but is *conservative*: in
guarded/critical situations it drops EVERY update proposal, including correct ones — and Phase 3.5
showed many of those blocks are rule false positives (the answer quarantines a bad claim, the
token-overlap check misreads it as reuse). Running a semantic judge on every answer would be slow and
costly; running it never leaves the over-blocking in place.

The resolution is two tiers:

  * **Tier 1 (always, deterministic, free):** the rule verifier + ``update_allowed_after_verifier``.
    This is the runtime gate; it never calls a model.
  * **Tier 2 (only on a CRITICAL state-update, and only if a semantic judge is wired):** the expensive
    LLM-as-judge adjudicates. It can BLOCK a tier-1-allowed update when the answer genuinely adopts a
    bad claim (catches a rule false negative), and RECOVER a tier-1-blocked update when the answer is
    semantically clean and the rule block was a false positive (the cost ChatGPT warned about).

Layer-9's gate remains the final authority on the actual mutation — this only decides whether a
*proposal* is forwarded. The default runtime path is unchanged and deterministic: with no semantic_fn,
or on a non-critical commit, only Tier 1 runs.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from desi_router.governance.modes import RouterDecision, update_allowed_after_verifier
from desi_router.governance.report import DesiReport
from desi_router.governance.verifier import VerifierResult

# a semantic judge: (answer, claim) -> "adopts" | "rejects" | "absent". Injected so runtime stays
# deterministic unless the caller explicitly wires a model-backed judge.
SemanticFn = Callable[[str, str], str]


@dataclass
class GateResult:
    update_proposal_allowed: bool          # may this answer FORWARD a persistent-update proposal?
    tier: str                              # "tier1_only" | "tier2_semantic"
    rule_ok: bool
    critical: bool
    semantic_checked: bool = False
    semantic_adopts: bool | None = None    # None if tier 2 did not run
    reason: str = ""


def is_critical_update(report: DesiReport, decision: RouterDecision) -> bool:
    """Deterministic: would a wrong commit here pollute canonical Layer-9 state? Critical iff the
    situation involves invalidated/superseded material or an open conflict the answer would resolve.
    Non-critical commits never pay for the expensive tier."""
    return bool(report.invalidated_claim_ids or report.superseded_claim_ids
                or report.task_touches_invalidated
                or (report.open_conflict_ids and report.answer_requires_conflict_resolution))


def decide_commit(report: DesiReport, decision: RouterDecision, answer: str, *,
                  rule_result: VerifierResult, semantic_fn: SemanticFn | None = None) -> GateResult:
    """Combine the two tiers into one 'may forward an update proposal?' decision."""
    rule_ok = rule_result.ok
    tier1 = update_allowed_after_verifier(decision, rule_ok)
    critical = is_critical_update(report, decision)

    bad_claims = tuple(report.invalidated_claim_texts) + tuple(report.superseded_claim_texts)
    if semantic_fn is None or not critical or not bad_claims:
        return GateResult(tier1, "tier1_only", rule_ok, critical,
                          reason="deterministic gate only (non-critical or no semantic judge)")

    # --- Tier 2: expensive semantic adjudication on a critical commit -----------------------------
    # On a critical commit the semantic judge is the authority for "may forward a proposal?": it BLOCKS
    # when the answer genuinely adopts a bad claim (catching a rule false negative) and CLEARS otherwise
    # — recovering the conservative Tier-1 block that drops correct updates (the over-blocking cost).
    # Layer-9's gate still decides the actual mutation; this only forwards a proposal.
    adopts = any(semantic_fn(answer, c) == "adopts" for c in bad_claims)
    allowed = not adopts
    recovered = allowed and not tier1
    reason = ("semantic judge: answer adopts an invalidated/superseded claim -> block" if adopts
              else "semantic judge cleared the answer; recovered a conservative Tier-1 block" if recovered
              else "semantic judge cleared the answer (Tier 1 already allowed)")
    return GateResult(allowed, "tier2_semantic", rule_ok, critical, semantic_checked=True,
                      semantic_adopts=adopts, reason=reason)
