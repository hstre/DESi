"""Tests for v0.7 metric-aware Jury — Integrator vetoes on regression."""
from __future__ import annotations

from desi.eval import scenario_by_id
from desi.evolution import (
    CloneSandbox,
    DelphiJury,
    JuryRole,
    MetricsDelta,
    MutationProposal,
    MutationTarget,
    PairedMutationEvaluation,
    PathQualityMetrics,
    ReflectionEngine,
    ReflectionReport,
    Vote,
    m_001,
)
from desi.evolution.evaluation import MutationEvaluation
from desi.evolution.paired_evaluation import (
    PairedEvaluationReport,
    PairedScenarioOutcome,
)
from desi.evolution.sandbox import default_stable


def _paired_with_verdict(verdict: str) -> PairedEvaluationReport:
    """Hand-craft a paired report with a chosen aggregate verdict."""
    if verdict == "improved":
        stable = PathQualityMetrics(
            scenario_id="ADV_BRANCH_EXPLOSION",
            timeline_length=27, branch_opened_count=4,
            guard_blocked_count=2, contradicts_count=0,
            merged_into_count=0, hook_error_count=0,
        )
        clone = PathQualityMetrics(
            scenario_id="ADV_BRANCH_EXPLOSION",
            timeline_length=27, branch_opened_count=3,
            guard_blocked_count=3, contradicts_count=0,
            merged_into_count=0, hook_error_count=0,
        )
    elif verdict == "regressed":
        stable = PathQualityMetrics(
            scenario_id="S2", timeline_length=25, branch_opened_count=3,
            guard_blocked_count=0, contradicts_count=2,
            merged_into_count=0, hook_error_count=0,
        )
        clone = PathQualityMetrics(
            scenario_id="S2", timeline_length=25, branch_opened_count=3,
            guard_blocked_count=0, contradicts_count=0,  # CONTRADICTS lost
            merged_into_count=0, hook_error_count=0,
        )
    else:  # neutral
        m = PathQualityMetrics(
            scenario_id="S2", timeline_length=25, branch_opened_count=3,
            guard_blocked_count=0, contradicts_count=2,
            merged_into_count=0, hook_error_count=0,
        )
        stable = m
        clone = m
    return PairedEvaluationReport(
        mutation_id="M-test",
        clone_id="clone_x",
        stable_version="stable-v0.5.0",
        timestamp=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc),
        stable_config={},
        clone_config={},
        outcomes=[PairedScenarioOutcome(
            scenario_id=stable.scenario_id,
            stable_result=None,    # type: ignore
            clone_result=None,     # type: ignore
            stable_metrics=stable,
            clone_metrics=clone,
            delta=MetricsDelta(stable=stable, clone=clone),
        )],
    )


def _stub_proposal() -> MutationProposal:
    return MutationProposal(
        parent_version="stable-v0.5.0",
        problem="x", hypothesis="y",
        target=MutationTarget.BRANCH_HEURISTICS,
        config_delta={"guard_thresholds.branch_open_evidence_min": 0.45},
        expected_improvement="z",
        rollback_conditions=("revert if y",),
        motivating_findings=("rf_x",),
    )


def _refl() -> ReflectionReport:
    return ReflectionReport(
        evaluation_id="eval_x", scenario_id="N/A", findings=(),
    )


def _eval(proposal):
    stable = default_stable()
    clone = CloneSandbox(stable)
    clone.apply(proposal)
    return MutationEvaluation(seed=11).run(clone, proposal.mutation_id)


# ---------------------------------------------------------------------------
# Integrator on paired_report=improved → APPROVE
# ---------------------------------------------------------------------------


def test_integrator_approves_when_paired_verdict_improved() -> None:
    p = _stub_proposal()
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(),
        paired_report=_paired_with_verdict("improved"),
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.APPROVE


def test_integrator_vetos_when_paired_verdict_regressed() -> None:
    p = _stub_proposal()
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(),
        paired_report=_paired_with_verdict("regressed"),
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.VETO
    assert integrator.veto is not None
    assert integrator.veto.is_valid
    assert "regressed" in integrator.rationale.lower()


def test_integrator_revises_when_paired_verdict_neutral() -> None:
    p = _stub_proposal()
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(),
        paired_report=_paired_with_verdict("neutral"),
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.REVISE


def test_jury_without_paired_report_behaves_like_v06() -> None:
    """The v0.7 paired_report kwarg is optional. v0.6-style callers
    that omit it must see the same decision they would have seen
    before."""
    p = _stub_proposal()
    a = DelphiJury().deliberate(p, _eval(p), _refl())
    b = DelphiJury().deliberate(p, _eval(p), _refl(), paired_report=None)
    a_signature = [(v.role, v.vote) for v in a.round2_votes]
    b_signature = [(v.role, v.vote) for v in b.round2_votes]
    assert a_signature == b_signature
