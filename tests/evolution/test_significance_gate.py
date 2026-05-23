"""Tests for v0.8 SignificanceGate — 4/5 pass, 3/5 inconclusive, 1 regression fail."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.evolution import (
    MetricsDelta,
    MultiSeedEvaluationReport,
    PathQualityMetrics,
    ScenarioAggregate,
    SignificanceDecision,
    SignificanceGate,
)


def _agg(scenario_id: str, verdicts: tuple[str, ...]) -> ScenarioAggregate:
    return ScenarioAggregate(
        scenario_id=scenario_id,
        n_seeds=len(verdicts),
        mean_branch_delta=0.0,
        median_branch_delta=0.0,
        std_branch_delta=0.0,
        mean_timeline_delta=0.0,
        median_timeline_delta=0.0,
        std_timeline_delta=0.0,
        mean_guard_delta=0.0,
        per_seed_verdicts=verdicts,
    )


def _report(
    *,
    candidate_verdicts: tuple[str, ...] = ("improved",) * 5,
    s2_verdicts: tuple[str, ...] = ("neutral",) * 5,
    s6_verdicts: tuple[str, ...] = ("neutral",) * 5,
    seeds: tuple[int, ...] = (42, 43, 44, 45, 46),
) -> MultiSeedEvaluationReport:
    """Hand-craft a multi-seed report with prescribed per-seed verdicts."""
    return MultiSeedEvaluationReport(
        mutation_id="M-test",
        clone_id="clone_x",
        parent_version="stable-v0.5.0",
        timestamp=datetime.now(timezone.utc),
        scenario_ids=("ADV_BRANCH_EXPLOSION", "S2", "S6"),
        seeds=seeds,
        per_seed_reports=(),
        aggregates={
            "ADV_BRANCH_EXPLOSION": _agg("ADV_BRANCH_EXPLOSION",
                                         candidate_verdicts),
            "S2": _agg("S2", s2_verdicts),
            "S6": _agg("S6", s6_verdicts),
        },
    )


# ---------------------------------------------------------------------------
# 4/5 improved → pass
# ---------------------------------------------------------------------------


def test_four_of_five_improved_passes() -> None:
    r = _report(candidate_verdicts=("improved", "improved", "improved",
                                    "improved", "neutral"))
    d = SignificanceGate().decide(r)
    assert d.verdict == "improved"
    assert len(d.supporting_seeds) == 4


def test_five_of_five_improved_passes() -> None:
    r = _report(candidate_verdicts=("improved",) * 5)
    d = SignificanceGate().decide(r)
    assert d.verdict == "improved"
    assert d.supporting_seeds == (42, 43, 44, 45, 46)


# ---------------------------------------------------------------------------
# 3/5 improved → inconclusive
# ---------------------------------------------------------------------------


def test_three_of_five_improved_is_inconclusive() -> None:
    r = _report(candidate_verdicts=("improved", "improved", "improved",
                                    "neutral", "neutral"))
    d = SignificanceGate().decide(r)
    assert d.verdict == "inconclusive"
    # Inconclusive surfaces the seeds that *did* support, so the
    # next pass can compare.
    assert set(d.supporting_seeds) == {42, 43, 44}


def test_one_of_five_improved_is_inconclusive() -> None:
    r = _report(candidate_verdicts=("improved", "neutral", "neutral",
                                    "neutral", "neutral"))
    d = SignificanceGate().decide(r)
    assert d.verdict == "inconclusive"


def test_zero_of_five_improved_is_neutral_not_inconclusive() -> None:
    """If the mutation does nothing, there is no improvement to assert,
    but there is also no regression — so the gate reports neutral.
    """
    r = _report(candidate_verdicts=("neutral",) * 5)
    d = SignificanceGate().decide(r)
    assert d.verdict == "neutral"


# ---------------------------------------------------------------------------
# Any regression on a guard or candidate → regressed
# ---------------------------------------------------------------------------


def test_one_regression_on_a_guard_fails_immediately() -> None:
    r = _report(
        candidate_verdicts=("improved",) * 5,
        s2_verdicts=("neutral", "neutral", "regressed", "neutral", "neutral"),
    )
    d = SignificanceGate().decide(r)
    assert d.verdict == "regressed"
    assert 44 in d.failing_seeds


def test_one_regression_on_the_candidate_fails_immediately() -> None:
    r = _report(
        candidate_verdicts=("improved", "improved", "improved",
                            "improved", "regressed"),
    )
    d = SignificanceGate().decide(r)
    assert d.verdict == "regressed"
    assert 46 in d.failing_seeds


def test_regression_on_s6_fails() -> None:
    r = _report(
        candidate_verdicts=("improved",) * 5,
        s6_verdicts=("regressed", "neutral", "neutral", "neutral", "neutral"),
    )
    d = SignificanceGate().decide(r)
    assert d.verdict == "regressed"
    assert 42 in d.failing_seeds


# ---------------------------------------------------------------------------
# Gate refuses wrong-size reports
# ---------------------------------------------------------------------------


def test_gate_refuses_report_with_wrong_seed_count() -> None:
    r = _report(
        candidate_verdicts=("improved", "improved", "improved", "improved"),
        s2_verdicts=("neutral",) * 4,
        s6_verdicts=("neutral",) * 4,
        seeds=(42, 43, 44, 45),
    )
    d = SignificanceGate().decide(r)
    assert d.verdict == "inconclusive"
    assert "5" in d.rationale  # mentions the required seed count


# ---------------------------------------------------------------------------
# Decision shape
# ---------------------------------------------------------------------------


def test_decision_to_dict_is_serialisable() -> None:
    r = _report()
    d = SignificanceGate().decide(r).to_dict()
    for k in ("mutation_id", "verdict", "supporting_seeds",
              "failing_seeds", "rationale"):
        assert k in d
    assert d["verdict"] in {"improved", "neutral", "regressed", "inconclusive"}


def test_decision_is_frozen_dataclass() -> None:
    import pytest
    d = SignificanceGate().decide(_report())
    with pytest.raises(Exception):
        d.verdict = "tampered"  # type: ignore
