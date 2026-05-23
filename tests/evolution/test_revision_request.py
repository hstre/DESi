"""Tests for v0.9 RevisionRequest — structured follow-up on inconclusive verdict."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from desi.evolution import (
    MultiSeedEvaluationReport,
    RevisionRequest,
    ScenarioAggregate,
    SignificanceDecision,
    SignificanceGate,
    build_revision_request,
)


def _agg(scenario_id: str, verdicts: tuple[str, ...]) -> ScenarioAggregate:
    return ScenarioAggregate(
        scenario_id=scenario_id,
        n_seeds=len(verdicts),
        mean_branch_delta=0.0, median_branch_delta=0.0,
        std_branch_delta=0.0, mean_timeline_delta=0.0,
        median_timeline_delta=0.0, std_timeline_delta=0.0,
        mean_guard_delta=0.0,
        per_seed_verdicts=verdicts,
    )


def _report(candidate_verdicts: tuple[str, ...]) -> MultiSeedEvaluationReport:
    return MultiSeedEvaluationReport(
        mutation_id="M-001",
        clone_id="clone_x",
        parent_version="stable-v0.5.0",
        timestamp=datetime.now(timezone.utc),
        scenario_ids=("ADV_BRANCH_EXPLOSION", "S2", "S6"),
        seeds=(42, 43, 44, 45, 46),
        per_seed_reports=(),
        aggregates={
            "ADV_BRANCH_EXPLOSION": _agg("ADV_BRANCH_EXPLOSION",
                                         candidate_verdicts),
            "S2": _agg("S2", ("neutral",) * 5),
            "S6": _agg("S6", ("neutral",) * 5),
        },
    )


# ---------------------------------------------------------------------------
# Inconclusive → request produced
# ---------------------------------------------------------------------------


def test_inconclusive_decision_yields_revision_request() -> None:
    report = _report(("improved", "improved", "improved",
                      "neutral", "neutral"))  # 3/5 improved
    decision = SignificanceGate().decide(report)
    assert decision.verdict == "inconclusive"
    request = build_revision_request(decision, report=report)
    assert isinstance(request, RevisionRequest)


def test_request_has_all_mandatory_fields() -> None:
    decision = SignificanceDecision(
        mutation_id="M-001", verdict="inconclusive",
        supporting_seeds=(42, 43, 44), failing_seeds=(45, 46),
        rationale="only 3/5 improved",
    )
    request = build_revision_request(decision)
    assert request.request_id  # non-empty
    assert request.mutation_id == "M-001"
    assert request.reason  # non-empty
    assert isinstance(request.failed_scenarios, tuple)
    assert request.failed_seeds == (45, 46)
    assert len(request.suggested_actions) >= 1


def test_request_id_is_deterministic() -> None:
    d = SignificanceDecision(
        mutation_id="M-001", verdict="inconclusive",
        supporting_seeds=(42,), failing_seeds=(43, 44),
        rationale="x",
    )
    a = build_revision_request(d)
    b = build_revision_request(d)
    assert a.request_id == b.request_id


def test_request_id_differs_when_inputs_differ() -> None:
    d1 = SignificanceDecision(
        mutation_id="M-001", verdict="inconclusive",
        supporting_seeds=(), failing_seeds=(43,),
        rationale="x",
    )
    d2 = SignificanceDecision(
        mutation_id="M-002", verdict="inconclusive",
        supporting_seeds=(), failing_seeds=(43,),
        rationale="x",
    )
    a = build_revision_request(d1)
    b = build_revision_request(d2)
    assert a.request_id != b.request_id


# ---------------------------------------------------------------------------
# Non-inconclusive verdicts raise
# ---------------------------------------------------------------------------


def test_build_revision_request_rejects_improved_decision() -> None:
    d = SignificanceDecision(
        mutation_id="M-001", verdict="improved",
        supporting_seeds=(42, 43, 44, 45, 46),
        failing_seeds=(), rationale="ok",
    )
    with pytest.raises(ValueError):
        build_revision_request(d)


def test_build_revision_request_rejects_regressed_decision() -> None:
    d = SignificanceDecision(
        mutation_id="M-001", verdict="regressed",
        supporting_seeds=(),
        failing_seeds=(43,),
        rationale="x",
    )
    with pytest.raises(ValueError):
        build_revision_request(d)


# ---------------------------------------------------------------------------
# Report-aware failed_scenarios
# ---------------------------------------------------------------------------


def test_failed_scenarios_drawn_from_report_when_provided() -> None:
    report = _report(("improved", "improved", "improved",
                      "neutral", "neutral"))
    decision = SignificanceGate().decide(report)
    request = build_revision_request(decision, report=report)
    assert "ADV_BRANCH_EXPLOSION" in request.failed_scenarios


def test_export_shape() -> None:
    d = SignificanceDecision(
        mutation_id="M-001", verdict="inconclusive",
        supporting_seeds=(42,), failing_seeds=(43, 44),
        rationale="x",
    )
    r = build_revision_request(d).to_dict()
    for k in ("request_id", "mutation_id", "reason",
              "failed_scenarios", "failed_seeds",
              "suggested_actions"):
        assert k in r


def test_revision_request_is_frozen() -> None:
    d = SignificanceDecision(
        mutation_id="M-001", verdict="inconclusive",
        supporting_seeds=(42,), failing_seeds=(43,),
        rationale="x",
    )
    r = build_revision_request(d)
    with pytest.raises(Exception):
        r.reason = "tampered"  # type: ignore
