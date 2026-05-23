"""Tests for v0.8 multi-seed-aware Jury.

Round 2 must consult the MultiSeedEvaluationReport (not just the
single-seed paired report). The Integrator approves on robust
improvement, revises on inconclusive, vetoes on regression.
"""
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
    PathQualityMetrics,
    ReflectionReport,
    ScenarioAggregate,
    Vote,
)
from desi.evolution.evaluation import MutationEvaluation
from desi.evolution.sandbox import default_stable


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


def _ms_report(
    *,
    candidate_verdicts: tuple[str, ...] = ("improved",) * 5,
    s2_verdicts: tuple[str, ...] = ("neutral",) * 5,
    s6_verdicts: tuple[str, ...] = ("neutral",) * 5,
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
                                         candidate_verdicts),
            "S2": _agg("S2", s2_verdicts),
            "S6": _agg("S6", s6_verdicts),
        },
    )


def _proposal() -> MutationProposal:
    return MutationProposal(
        parent_version="stable-v0.5.0",
        problem="branch overopen on explosion",
        hypothesis="raise the evidence floor",
        target=MutationTarget.BRANCH_HEURISTICS,
        config_delta={"guard_thresholds.branch_open_evidence_min": 0.45},
        expected_improvement="branch_opened_count -1 on adversarial",
        rollback_conditions=("revert if S2 contradicts drift",),
        motivating_findings=("rf_branch_overopen",),
    )


def _eval(p):
    clone = CloneSandbox(default_stable())
    clone.apply(p)
    return MutationEvaluation(seed=11).run(clone, p.mutation_id)


def _refl() -> ReflectionReport:
    return ReflectionReport(evaluation_id="eval_x", scenario_id="N/A",
                            findings=())


# ---------------------------------------------------------------------------
# Integrator on multi-seed verdicts
# ---------------------------------------------------------------------------


def test_integrator_approves_when_multi_seed_robust_improvement() -> None:
    p = _proposal()
    ms = _ms_report(candidate_verdicts=("improved",) * 5)
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=ms,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.APPROVE
    assert "multi-seed" in integrator.rationale.lower()


def test_integrator_revises_when_multi_seed_inconclusive() -> None:
    p = _proposal()
    # Only 3/5 improved on the candidate.
    ms = _ms_report(candidate_verdicts=("improved", "improved", "improved",
                                        "neutral", "neutral"))
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=ms,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.REVISE
    assert "inconclusive" in integrator.rationale.lower()


def test_integrator_vetos_when_multi_seed_regression() -> None:
    p = _proposal()
    ms = _ms_report(
        candidate_verdicts=("improved",) * 5,
        s2_verdicts=("neutral", "neutral", "regressed", "neutral", "neutral"),
    )
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=ms,
    )
    integrator = next(v for v in decision.round2_votes
                      if v.role is JuryRole.INTEGRATOR)
    assert integrator.vote is Vote.VETO
    assert integrator.veto is not None
    assert integrator.veto.is_valid
    assert "regress" in integrator.rationale.lower()


# ---------------------------------------------------------------------------
# Skeptiker robustness probe
# ---------------------------------------------------------------------------


def test_skeptiker_revises_on_non_robust_improvement() -> None:
    """Even if no regression, an improvement on only 3/5 seeds is not
    robust enough for the Skeptiker to APPROVE."""
    p = _proposal()
    ms = _ms_report(candidate_verdicts=("improved", "improved", "improved",
                                        "neutral", "neutral"))
    decision = DelphiJury().deliberate(
        p, _eval(p), _refl(), multi_seed_report=ms,
    )
    skeptiker = next(v for v in decision.round2_votes
                     if v.role is JuryRole.SKEPTIKER)
    assert skeptiker.vote is Vote.REVISE
    assert "robust" in skeptiker.rationale.lower()


# ---------------------------------------------------------------------------
# Backwards compatibility — no multi_seed_report → v0.7 behaviour
# ---------------------------------------------------------------------------


def test_jury_without_multi_seed_report_matches_v07_signature() -> None:
    """The v0.8 multi_seed_report kwarg is optional. Callers that omit
    it must see the same decision they would have seen in v0.7."""
    p = _proposal()
    a = DelphiJury().deliberate(p, _eval(p), _refl())
    b = DelphiJury().deliberate(p, _eval(p), _refl(), multi_seed_report=None)
    a_sig = [(v.role, v.vote) for v in a.round2_votes]
    b_sig = [(v.role, v.vote) for v in b.round2_votes]
    assert a_sig == b_sig
