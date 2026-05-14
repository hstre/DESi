"""Tests for ProposalDraftBuilder."""
from __future__ import annotations

from desi.eval import EvaluationHarness, scenario_by_id
from desi.evolution import (
    MutationProposal,
    MutationTarget,
    ProposalDraftBuilder,
    ReflectionEngine,
    ReflectionFinding,
)


def _finding(
    *,
    affected_components: tuple[str, ...] = ("branch_heuristics",),
    category: str = "performance",
) -> ReflectionFinding:
    return ReflectionFinding(
        category=category,
        observed_problem="branches open too eagerly",
        suspected_root_cause="evidence threshold too low",
        affected_components=affected_components,
        confidence=0.6,
        supporting_events=(3, 7, 11),
    )


def test_draft_returns_a_proposal_marked_as_requires_ratification() -> None:
    builder = ProposalDraftBuilder(default_stable_version="stable-v0.5.0")
    proposal = builder.draft(_finding())
    assert isinstance(proposal, MutationProposal)
    assert proposal.requires_ratification is True


def test_draft_picks_branch_heuristics_nudge_when_component_matches() -> None:
    builder = ProposalDraftBuilder(default_stable_version="stable-v0.5.0")
    proposal = builder.draft(_finding(
        affected_components=("branch_heuristics",),
    ))
    assert proposal.target is MutationTarget.BRANCH_HEURISTICS
    assert "guard_thresholds.branch_open_evidence_min" in proposal.config_delta


def test_draft_picks_merge_policy_nudge() -> None:
    builder = ProposalDraftBuilder(default_stable_version="stable-v0.5.0")
    proposal = builder.draft(_finding(
        affected_components=("merge_policy",),
    ))
    assert proposal.target is MutationTarget.MERGE_POLICY


def test_draft_falls_back_to_empty_delta_when_no_component_matches() -> None:
    builder = ProposalDraftBuilder(default_stable_version="stable-v0.5.0")
    proposal = builder.draft(_finding(
        affected_components=("something_unknown",),
    ))
    assert proposal.config_delta == {}
    assert proposal.requires_ratification is True


def test_draft_records_motivating_finding_id_when_supplied() -> None:
    builder = ProposalDraftBuilder(default_stable_version="stable-v0.5.0")
    proposal = builder.draft(_finding(), motivating_finding_id="rf_42")
    assert "rf_42" in proposal.motivating_findings


def test_draft_proposal_is_not_promotable_until_ratified() -> None:
    """promote() refuses unratified drafts."""
    from desi.evolution import promote, PromotionError
    builder = ProposalDraftBuilder(default_stable_version="stable-v0.5.0")
    draft = builder.draft(_finding())
    # Build minimal stubs for clone / eval / jury so promote can
    # reach the ratification check.
    class _StubClone:
        class _StubStable:
            version = "stable-v0.5.0"
            as_dict = {}
            knobs = ()
        stable = _StubStable()
    class _StubEval:
        passed_pflicht = True
        passed_adversarial = True
        passed_regression = True
        all_green = True
        performance_delta = 0.0
        path_quality_delta = 0.0
    class _StubJury:
        valid_vetos: list = []
        approve_count = 5
        revise_count = 0
        quorum_reached = True
    import pytest as _pytest
    with _pytest.raises(PromotionError) as excinfo:
        promote(draft, _StubClone(), _StubEval(), _StubJury())
    assert "requires_ratification" in str(excinfo.value)
