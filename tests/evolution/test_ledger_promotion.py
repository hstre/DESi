"""Tests for promote_with_ledger — audit-trail completeness gating."""
from __future__ import annotations

import pytest

from desi.evolution import (
    EvolutionLedger,
    JuryRole,
    LedgerEventType,
    MutationProposal,
    MutationTarget,
    ObligationStatus,
    PromotionError,
    Veto,
    VetoToTestSynthesiser,
    Vote,
    promote_with_ledger,
)
from desi.evolution.jury import (
    JuryDecision,
    JuryFinalVote,
    JuryReview,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_approve_decision() -> JuryDecision:
    return JuryDecision(
        round1_reviews=tuple(
            JuryReview(role=role, summary="x", concerns=(),
                       suggestions=(), confidence=0.5)
            for role in JuryRole
        ),
        round2_votes=tuple(
            JuryFinalVote(role=role, vote=Vote.APPROVE, rationale="ok")
            for role in JuryRole
        ),
    )


def _seed_complete_ledger(
    ledger: EvolutionLedger,
    proposal: MutationProposal,
) -> None:
    """Append the four pre-promotion entries the ledger gate requires."""
    ledger.append(LedgerEventType.PROPOSAL, {
        "mutation_id": proposal.mutation_id,
        "target": proposal.target.value,
    })
    ledger.append(LedgerEventType.EVALUATION, {
        "mutation_id": proposal.mutation_id,
        "all_green": True,
    })
    ledger.append(LedgerEventType.JURY_ROUND1, {
        "mutation_id": proposal.mutation_id,
        "reviews": 5,
    })
    ledger.append(LedgerEventType.JURY_ROUND2, {
        "mutation_id": proposal.mutation_id,
        "approve_count": 5,
    })


# ---------------------------------------------------------------------------
# Gate fails on missing entries
# ---------------------------------------------------------------------------


def test_promote_blocked_when_proposal_entry_missing(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    ledger = EvolutionLedger()
    # Skip the PROPOSAL entry; everything else present.
    ledger.append(LedgerEventType.EVALUATION,
                  {"mutation_id": proposal_with_delta.mutation_id})
    ledger.append(LedgerEventType.JURY_ROUND2,
                  {"mutation_id": proposal_with_delta.mutation_id})
    with pytest.raises(PromotionError) as e:
        promote_with_ledger(
            proposal_with_delta, clone, evaluation_report,
            _all_approve_decision(), ledger,
        )
    assert any("PROPOSAL" in r for r in e.value.reasons)


def test_promote_blocked_when_evaluation_entry_missing(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.PROPOSAL,
                  {"mutation_id": proposal_with_delta.mutation_id})
    ledger.append(LedgerEventType.JURY_ROUND2,
                  {"mutation_id": proposal_with_delta.mutation_id})
    with pytest.raises(PromotionError) as e:
        promote_with_ledger(
            proposal_with_delta, clone, evaluation_report,
            _all_approve_decision(), ledger,
        )
    assert any("EVALUATION" in r for r in e.value.reasons)


def test_promote_blocked_when_jury_entry_missing(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.PROPOSAL,
                  {"mutation_id": proposal_with_delta.mutation_id})
    ledger.append(LedgerEventType.EVALUATION,
                  {"mutation_id": proposal_with_delta.mutation_id})
    with pytest.raises(PromotionError) as e:
        promote_with_ledger(
            proposal_with_delta, clone, evaluation_report,
            _all_approve_decision(), ledger,
        )
    assert any("JURY_ROUND2" in r for r in e.value.reasons)


# ---------------------------------------------------------------------------
# Open obligations block promotion
# ---------------------------------------------------------------------------


def test_promote_blocked_when_obligation_is_open(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    ledger = EvolutionLedger()
    _seed_complete_ledger(ledger, proposal_with_delta)
    veto = Veto(
        role=JuryRole.ADVERSARIAL,
        affected_claim="branch_heuristics",
        suspected_risk="reg",
        failure_case="ADV_BRANCH_EXPLOSION will fail",
        proposed_test="re-run ADV",
    )
    obl = VetoToTestSynthesiser().synthesise(veto)
    ledger.append(LedgerEventType.VETO_VALID, {
        "mutation_id": proposal_with_delta.mutation_id,
        "veto_role": veto.role.value,
    })
    ledger.append(LedgerEventType.VETO_OBLIGATION, {
        "mutation_id": proposal_with_delta.mutation_id,
        "obligation_id": obl.obligation_id,
        "status": obl.status.value,
    })
    with pytest.raises(PromotionError) as e:
        promote_with_ledger(
            proposal_with_delta, clone, evaluation_report,
            _all_approve_decision(), ledger,
        )
    assert any("unresolved veto obligation" in r for r in e.value.reasons)


def test_promote_proceeds_when_obligation_passes(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    ledger = EvolutionLedger()
    _seed_complete_ledger(ledger, proposal_with_delta)
    veto = Veto(
        role=JuryRole.ADVERSARIAL,
        affected_claim="branch_heuristics",
        suspected_risk="reg",
        failure_case="ADV_BRANCH_EXPLOSION will fail",
        proposed_test="re-run ADV",
    )
    obl = VetoToTestSynthesiser().synthesise(veto)
    ledger.append(LedgerEventType.VETO_OBLIGATION, {
        "mutation_id": proposal_with_delta.mutation_id,
        "obligation_id": obl.obligation_id,
        "status": obl.status.value,
    })
    # Append a status-change entry moving the obligation to PASSED.
    ledger.append(LedgerEventType.OBLIGATION_STATUS_CHANGE, {
        "mutation_id": proposal_with_delta.mutation_id,
        "obligation_id": obl.obligation_id,
        "new_status": ObligationStatus.PASSED.value,
    })
    result = promote_with_ledger(
        proposal_with_delta, clone, evaluation_report,
        _all_approve_decision(), ledger,
    )
    assert result.new_stable.version != clone.stable.version
    # Ledger gained SNAPSHOT + PROMOTION_DECISION entries.
    types = [e.event_type for e in ledger.entries()]
    assert LedgerEventType.SNAPSHOT in types
    assert LedgerEventType.PROMOTION_DECISION in types


# ---------------------------------------------------------------------------
# Append-only after promotion
# ---------------------------------------------------------------------------


def test_promotion_does_not_mutate_prior_entries(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    ledger = EvolutionLedger()
    _seed_complete_ledger(ledger, proposal_with_delta)
    baseline = ledger.entries()
    promote_with_ledger(
        proposal_with_delta, clone, evaluation_report,
        _all_approve_decision(), ledger,
    )
    assert ledger.verify_append_only(baseline)
