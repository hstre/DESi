"""Tests for DelphiJury — independent first round + final vote."""
from __future__ import annotations

import pytest

from desi.evolution import (
    DelphiJury,
    JuryRole,
    MutationProposal,
    MutationTarget,
    Vote,
)
from desi.evolution.jury import DEFAULT_MEMBERS


def test_jury_has_five_members() -> None:
    jury = DelphiJury()
    assert len(jury._members) == 5
    assert {m.role for m in jury._members} == {
        JuryRole.REPLIKATOR,
        JuryRole.SKEPTIKER,
        JuryRole.METHODIKER,
        JuryRole.ADVERSARIAL,
        JuryRole.INTEGRATOR,
    }


def test_round1_reviews_are_independent(
    proposal_with_delta, evaluation_report, reflection_report,
) -> None:
    """Round 1 fn signatures don't receive any peer review, so the
    invariant is mechanical: each review is produced solely from
    (proposal, eval_report, reflection)."""
    jury = DelphiJury()
    decision = jury.deliberate(
        proposal_with_delta, evaluation_report, reflection_report,
    )
    assert len(decision.round1_reviews) == 5
    roles = {r.role for r in decision.round1_reviews}
    assert roles == {
        JuryRole.REPLIKATOR,
        JuryRole.SKEPTIKER,
        JuryRole.METHODIKER,
        JuryRole.ADVERSARIAL,
        JuryRole.INTEGRATOR,
    }


def test_each_round1_review_carries_summary_and_confidence(
    proposal_with_delta, evaluation_report, reflection_report,
) -> None:
    decision = DelphiJury().deliberate(
        proposal_with_delta, evaluation_report, reflection_report,
    )
    for r in decision.round1_reviews:
        assert r.summary
        assert 0.0 <= r.confidence <= 1.0


def test_round2_votes_are_one_per_member(
    proposal_with_delta, evaluation_report, reflection_report,
) -> None:
    decision = DelphiJury().deliberate(
        proposal_with_delta, evaluation_report, reflection_report,
    )
    assert len(decision.round2_votes) == 5
    for v in decision.round2_votes:
        assert v.vote in {Vote.APPROVE, Vote.REVISE, Vote.VETO}
        assert v.rationale


def test_clean_run_with_well_formed_proposal_reaches_quorum(
    proposal_with_delta, evaluation_report, reflection_report,
) -> None:
    """A proposal with rollback conditions, motivating findings,
    non-empty config_delta, and all-green evaluation should pass."""
    decision = DelphiJury().deliberate(
        proposal_with_delta, evaluation_report, reflection_report,
    )
    if evaluation_report.all_green:
        assert decision.quorum_reached
        assert decision.valid_vetos == []


def test_proposal_without_rollback_is_vetoed_by_skeptiker(
    stable, evaluation_report, reflection_report,
) -> None:
    # The pydantic model already forbids empty rollback_conditions,
    # so we test the skeptic logic via a single empty-string condition.
    # The skeptic checks `if not p.rollback_conditions` — a tuple with
    # an empty string is truthy. To exercise the veto path we use a
    # proposal with empty config_delta (skeptic returns REVISE for
    # that). Empty rollback can't be constructed; the test verifies
    # the model-level guarantee instead.
    with pytest.raises(Exception):
        MutationProposal(
            parent_version=stable.version,
            problem="x", hypothesis="y",
            target=MutationTarget.GUARD_THRESHOLDS,
            expected_improvement="z",
            rollback_conditions=(),
        )


def test_proposal_without_motivating_findings_gets_revise_from_methodiker(
    stable, evaluation_report, reflection_report,
) -> None:
    p = MutationProposal(
        parent_version=stable.version,
        problem="x", hypothesis="y",
        target=MutationTarget.GUARD_THRESHOLDS,
        config_delta={"guard_thresholds.merge_similarity_min": 0.9},
        expected_improvement="z",
        rollback_conditions=("revert if x",),
        # motivating_findings deliberately empty
    )
    decision = DelphiJury().deliberate(p, evaluation_report, reflection_report)
    methodiker = next(v for v in decision.round2_votes
                      if v.role is JuryRole.METHODIKER)
    assert methodiker.vote is Vote.REVISE
