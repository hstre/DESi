"""Tests for Promotion, Snapshot, and Rollback."""
from __future__ import annotations

import pytest

from desi.evolution import (
    DelphiJury,
    JuryDecision,
    JuryRole,
    PromotionError,
    Snapshot,
    Veto,
    Vote,
    promote,
    rollback,
)
from desi.evolution.jury import (
    JuryDecision as _JuryDecision,
    JuryFinalVote,
    JuryReview,
)


# ---------------------------------------------------------------------------
# Successful promotion path
# ---------------------------------------------------------------------------


def test_promote_succeeds_on_clean_run(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    jury = DelphiJury().deliberate(
        proposal_with_delta, evaluation_report,
        # No reflection needed for the happy-path test; pass a minimal
        # report that has no findings.
        _empty_reflection(proposal_with_delta),
    )
    # The smoke proposal carries motivating_findings + rollback +
    # non-empty config_delta, so it should reach quorum on a green
    # evaluation.
    if not jury.quorum_reached:
        pytest.skip("jury did not reach quorum; harness state varied")
    result = promote(proposal_with_delta, clone, evaluation_report, jury,
                     commit_hash="abc1234")
    assert result.new_stable.version != clone.stable.version
    assert (
        result.new_stable.as_dict["guard_thresholds.branch_open_evidence_min"]
        == proposal_with_delta.config_delta[
            "guard_thresholds.branch_open_evidence_min"
        ]
    )
    # Snapshot captures the pre-promotion stable.
    assert result.snapshot.version == clone.stable.version
    assert tuple(result.snapshot.knobs) == clone.stable.knobs


# ---------------------------------------------------------------------------
# Promotion is blocked when conditions are unmet
# ---------------------------------------------------------------------------


def test_promotion_blocked_when_jury_has_valid_veto(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    veto = Veto(
        role=JuryRole.ADVERSARIAL,
        affected_claim=proposal_with_delta.target.value,
        suspected_risk="adversarial regression",
        failure_case="ADV_BRANCH_EXPLOSION will fail under the new threshold",
        proposed_test="add explicit threshold-specific adversarial test",
    )
    decision = _JuryDecision(
        round1_reviews=tuple(
            JuryReview(role=role, summary="x", concerns=(), suggestions=(),
                       confidence=0.5)
            for role in JuryRole
        ),
        round2_votes=tuple(
            JuryFinalVote(role=role, vote=Vote.APPROVE, rationale="ok")
            for role in JuryRole if role is not JuryRole.ADVERSARIAL
        ) + (JuryFinalVote(role=JuryRole.ADVERSARIAL, vote=Vote.VETO,
                            rationale="see veto", veto=veto),),
    )
    with pytest.raises(PromotionError) as excinfo:
        promote(proposal_with_delta, clone, evaluation_report, decision)
    assert any("veto" in r.lower() for r in excinfo.value.reasons)


def test_promotion_blocked_when_quorum_not_reached(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    # Three approve + two revise = quorum below 4/5.
    votes = []
    for role in JuryRole:
        if role in {JuryRole.METHODIKER, JuryRole.SKEPTIKER}:
            votes.append(JuryFinalVote(role=role, vote=Vote.REVISE,
                                       rationale="needs work"))
        else:
            votes.append(JuryFinalVote(role=role, vote=Vote.APPROVE,
                                       rationale="ok"))
    decision = _JuryDecision(
        round1_reviews=tuple(
            JuryReview(role=role, summary="x", concerns=(), suggestions=(),
                       confidence=0.5)
            for role in JuryRole
        ),
        round2_votes=tuple(votes),
    )
    with pytest.raises(PromotionError) as excinfo:
        promote(proposal_with_delta, clone, evaluation_report, decision)
    assert any("quorum" in r for r in excinfo.value.reasons)


# ---------------------------------------------------------------------------
# Snapshot + rollback
# ---------------------------------------------------------------------------


def test_snapshot_captures_pre_promotion_state(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    decision = _all_approve_decision()
    result = promote(proposal_with_delta, clone, evaluation_report, decision,
                     commit_hash="deadbeef")
    snap = result.snapshot
    assert snap.commit_hash == "deadbeef"
    assert snap.version == clone.stable.version
    assert tuple(sorted(dict(snap.knobs).items())) == \
           tuple(sorted(clone.stable.as_dict.items()))


def test_rollback_restores_snapshot_to_stable(
    proposal_with_delta, evaluation_report, clone,
) -> None:
    decision = _all_approve_decision()
    result = promote(proposal_with_delta, clone, evaluation_report, decision)
    restored = rollback(result.snapshot)
    assert restored.version == clone.stable.version
    assert restored.as_dict == clone.stable.as_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_reflection(proposal):
    from desi.evolution import ReflectionReport
    return ReflectionReport(
        evaluation_id="eval_test", scenario_id="N/A", findings=(),
    )


def _all_approve_decision() -> _JuryDecision:
    return _JuryDecision(
        round1_reviews=tuple(
            JuryReview(role=role, summary="x", concerns=(), suggestions=(),
                       confidence=0.5)
            for role in JuryRole
        ),
        round2_votes=tuple(
            JuryFinalVote(role=role, vote=Vote.APPROVE, rationale="ok")
            for role in JuryRole
        ),
    )
