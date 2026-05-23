"""Tests for v0.9 stress-seed CONCERN — soft veto path in the Integrator."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.evolution import (
    CloneSandbox,
    DelphiJury,
    JuryRole,
    MetricsDelta,
    MultiSeedEvaluationReport,
    MutationProposal,
    MutationTarget,
    PairedScenarioOutcome,
    PathQualityMetrics,
    ReflectionReport,
    ScenarioAggregate,
    Vote,
)
from desi.evolution.evaluation import MutationEvaluation
from desi.evolution.sandbox import default_stable


# ---------------------------------------------------------------------------
# Vote.CONCERN is in the enum
# ---------------------------------------------------------------------------


def test_concern_is_in_vote_enum() -> None:
    assert Vote.CONCERN.value == "concern"


def test_concern_is_distinct_from_approve_revise_veto() -> None:
    others = {Vote.APPROVE, Vote.REVISE, Vote.VETO}
    assert Vote.CONCERN not in others


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _agg(scenario_id: str, verdicts: tuple[str, ...]) -> ScenarioAggregate:
    return ScenarioAggregate(
        scenario_id=scenario_id,
        n_seeds=len(verdicts),
        mean_branch_delta=-1.0 if "improved" in verdicts else 0.0,
        median_branch_delta=-1.0 if "improved" in verdicts else 0.0,
        std_branch_delta=0.0,
        mean_timeline_delta=0.0,
        median_timeline_delta=0.0,
        std_timeline_delta=0.0,
        mean_guard_delta=0.0,
        per_seed_verdicts=verdicts,
    )


def _make_stress_outcome(verdict: str) -> PairedScenarioOutcome:
    stable = PathQualityMetrics(
        scenario_id="ADV_BRANCH_EXPLOSION",
        timeline_length=27, branch_opened_count=4, guard_blocked_count=2,
        contradicts_count=0, merged_into_count=0, hook_error_count=0,
    )
    if verdict == "regressed":
        clone = PathQualityMetrics(
            scenario_id="ADV_BRANCH_EXPLOSION",
            timeline_length=27, branch_opened_count=5,  # MORE branches
            guard_blocked_count=1,
            contradicts_count=0, merged_into_count=0, hook_error_count=0,
        )
    elif verdict == "improved":
        clone = PathQualityMetrics(
            scenario_id="ADV_BRANCH_EXPLOSION",
            timeline_length=27, branch_opened_count=3,
            guard_blocked_count=3,
            contradicts_count=0, merged_into_count=0, hook_error_count=0,
        )
    else:  # neutral
        clone = stable
    return PairedScenarioOutcome(
        scenario_id="ADV_BRANCH_EXPLOSION",
        stable_result=None,    # type: ignore
        clone_result=None,     # type: ignore
        stable_metrics=stable,
        clone_metrics=clone,
        delta=MetricsDelta(stable=stable, clone=clone),
    )


def _make_report(
    *, mandatory_verdicts: tuple[str, ...] = ("improved",) * 5,
    stress_verdict: str | None = "improved",
) -> MultiSeedEvaluationReport:
    return MultiSeedEvaluationReport(
        mutation_id="M-test",
        clone_id="clone_x",
        parent_version="stable-v0.5.0",
        timestamp=datetime.now(timezone.utc),
        scenario_ids=("ADV_BRANCH_EXPLOSION", "S2", "S6"),
        seeds=(42, 43, 44, 45, 46),
        per_seed_reports=(),
        aggregates={
            "ADV_BRANCH_EXPLOSION": _agg("ADV_BRANCH_EXPLOSION",
                                         mandatory_verdicts),
            "S2": _agg("S2", ("neutral",) * 5),
            "S6": _agg("S6", ("neutral",) * 5),
        },
        stress_outcome=(
            _make_stress_outcome(stress_verdict)
            if stress_verdict is not None else None
        ),
    )


def _proposal() -> MutationProposal:
    return MutationProposal(
        parent_version="stable-v0.5.0",
        problem="branch overopen", hypothesis="raise evidence floor",
        target=MutationTarget.BRANCH_HEURISTICS,
        config_delta={"guard_thresholds.branch_open_evidence_min": 0.45},
        expected_improvement="branch_opened_count -1",
        rollback_conditions=("revert if S2 contradicts drift",),
        motivating_findings=("rf_branch_overopen",),
    )


def _eval(p):
    clone = CloneSandbox(default_stable())
    clone.apply(p)
    return MutationEvaluation(seed=11).run(clone, p.mutation_id)


def _refl():
    return ReflectionReport(evaluation_id="eval_x", scenario_id="N/A",
                            findings=())


# ---------------------------------------------------------------------------
# Integrator → CONCERN when stress regresses but mandatory seeds don't
# ---------------------------------------------------------------------------


def test_integrator_concern_when_stress_regresses_but_mandatory_does_not() -> None:
    p = _proposal()
    report = _make_report(
        mandatory_verdicts=("improved",) * 5,
        stress_verdict="regressed",
    )
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=report,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.CONCERN
    assert "stress" in integrator.rationale.lower()


def test_integrator_approves_when_stress_improves_and_mandatory_improves() -> None:
    """No CONCERN when stress mirrors the mandatory verdict."""
    p = _proposal()
    report = _make_report(stress_verdict="improved")
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=report,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.APPROVE


def test_integrator_approves_when_stress_outcome_is_absent() -> None:
    """No stress outcome → no CONCERN, just APPROVE."""
    p = _proposal()
    report = _make_report(stress_verdict=None)
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=report,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.APPROVE


def test_integrator_concern_does_not_carry_a_veto() -> None:
    """CONCERN is a soft veto — no structured Veto block attached."""
    p = _proposal()
    report = _make_report(
        mandatory_verdicts=("improved",) * 5,
        stress_verdict="regressed",
    )
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=report,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.veto is None


# ---------------------------------------------------------------------------
# CONCERN does not block mandatory regression — hard VETO still wins.
# ---------------------------------------------------------------------------


def test_mandatory_regression_still_vetos_over_stress_concern() -> None:
    p = _proposal()
    report = MultiSeedEvaluationReport(
        mutation_id="M-test",
        clone_id="clone_x",
        parent_version="stable-v0.5.0",
        timestamp=datetime.now(timezone.utc),
        scenario_ids=("ADV_BRANCH_EXPLOSION", "S2", "S6"),
        seeds=(42, 43, 44, 45, 46),
        per_seed_reports=(),
        aggregates={
            "ADV_BRANCH_EXPLOSION": _agg("ADV_BRANCH_EXPLOSION",
                                         ("improved",) * 5),
            "S2": _agg("S2", ("neutral", "neutral", "regressed",
                              "neutral", "neutral")),  # hard guard regression
            "S6": _agg("S6", ("neutral",) * 5),
        },
        stress_outcome=_make_stress_outcome("regressed"),
    )
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=report,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.VETO
    assert integrator.veto is not None
