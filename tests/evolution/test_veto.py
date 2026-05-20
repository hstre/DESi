"""Tests for the Veto protocol — valid vs invalid."""
from __future__ import annotations

import pytest

from desi.evolution import JuryRole, Veto, Vote
from desi.evolution.jury import JuryFinalVote


def _valid_veto() -> Veto:
    return Veto(
        role=JuryRole.SKEPTIKER,
        affected_claim="branch_heuristics",
        suspected_risk="silent regression",
        failure_case="branch_explosion adversarial pattern fails",
        proposed_test="re-run ADV_BRANCH_EXPLOSION and require pass",
    )


def test_valid_veto_carries_all_four_mandatory_fields() -> None:
    v = _valid_veto()
    assert v.is_valid
    assert v.affected_claim and v.suspected_risk
    assert v.failure_case and v.proposed_test


def test_veto_without_affected_claim_is_invalid() -> None:
    # pydantic min_length=1 rejects construction.
    with pytest.raises(Exception):
        Veto(
            role=JuryRole.SKEPTIKER,
            affected_claim="",
            suspected_risk="x",
            failure_case="y",
            proposed_test="z",
        )


def test_veto_without_risk_is_invalid() -> None:
    with pytest.raises(Exception):
        Veto(
            role=JuryRole.SKEPTIKER,
            affected_claim="x",
            suspected_risk="",
            failure_case="y",
            proposed_test="z",
        )


def test_veto_without_failure_case_is_invalid() -> None:
    with pytest.raises(Exception):
        Veto(
            role=JuryRole.SKEPTIKER,
            affected_claim="x",
            suspected_risk="y",
            failure_case="",
            proposed_test="z",
        )


def test_veto_without_proposed_test_is_invalid() -> None:
    with pytest.raises(Exception):
        Veto(
            role=JuryRole.SKEPTIKER,
            affected_claim="x",
            suspected_risk="y",
            failure_case="z",
            proposed_test="",
        )


def test_juryfinalvote_with_invalid_veto_is_discarded_by_decision() -> None:
    """If a member casts a VETO vote without a veto object, the
    JuryDecision.valid_vetos must NOT include it."""
    from desi.evolution.jury import JuryDecision, JuryReview
    # Construct a decision with one member-style vote that lacks veto.
    fake_vote = JuryFinalVote(
        role=JuryRole.SKEPTIKER,
        vote=Vote.VETO,
        rationale="I just don't like it",
        veto=None,
    )
    fake_review = JuryReview(
        role=JuryRole.SKEPTIKER,
        summary="x",
        concerns=(),
        suggestions=(),
        confidence=0.5,
    )
    decision = JuryDecision(
        round1_reviews=(fake_review,),
        round2_votes=(fake_vote,),
    )
    assert decision.valid_vetos == []
    assert len(decision.invalid_vetos) == 1


def test_juryfinalvote_with_valid_veto_is_counted() -> None:
    from desi.evolution.jury import JuryDecision, JuryReview
    valid = _valid_veto()
    fake_vote = JuryFinalVote(
        role=JuryRole.SKEPTIKER,
        vote=Vote.VETO,
        rationale="see veto",
        veto=valid,
    )
    fake_review = JuryReview(
        role=JuryRole.SKEPTIKER,
        summary="x",
        concerns=(),
        suggestions=(),
        confidence=0.5,
    )
    decision = JuryDecision(
        round1_reviews=(fake_review,),
        round2_votes=(fake_vote,),
    )
    assert decision.valid_vetos == [valid]
    assert decision.invalid_vetos == []
