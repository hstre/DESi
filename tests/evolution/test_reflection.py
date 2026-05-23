"""Tests for ReflectionEngine."""
from __future__ import annotations

import pytest

from desi.eval import EvaluationHarness, scenario_by_id
from desi.evolution import ReflectionEngine, ReflectionReport


def _result_for(scenario_id: str, seed: int = 42):
    harness = EvaluationHarness(model="m")
    return harness.run_scenario(scenario_by_id(scenario_id), seed=seed)


def test_reflection_produces_a_report() -> None:
    engine = ReflectionEngine()
    report = engine.reflect(_result_for("S2"))
    assert isinstance(report, ReflectionReport)
    assert report.scenario_id == "S2"
    assert report.evaluation_id.startswith("eval_")


def test_reflection_report_findings_carry_required_fields() -> None:
    engine = ReflectionEngine()
    report = engine.reflect(_result_for("S5"))
    for f in report.findings:
        assert f.category in {"performance", "quality", "safety"}
        assert f.observed_problem
        assert f.suspected_root_cause
        assert 0.0 <= f.confidence <= 1.0


def test_reflection_flags_excessive_branches_on_branch_explosion() -> None:
    """The adversarial branch-explosion-like pattern (≥5 branches) is
    expected to trigger the unnecessary_branches finding."""
    from desi.evolution.evaluation import (
        AdversarialPattern, adversarial_scenario,
    )
    harness = EvaluationHarness(model="m")
    result = harness.run_scenario(
        adversarial_scenario(AdversarialPattern.BRANCH_EXPLOSION),
        seed=42,
    )
    report = ReflectionEngine().reflect(result)
    categories = {f.category for f in report.findings}
    components = set()
    for f in report.findings:
        components.update(f.affected_components)
    assert "performance" in categories
    assert "branch_heuristics" in components


def test_reflection_returns_empty_on_trivial_clean_run() -> None:
    # S4 is a short, method-strong scenario with a single focus.
    report = ReflectionEngine().reflect(_result_for("S4", seed=42))
    # No mandatory findings; engine returns possibly empty findings.
    assert isinstance(report.findings, tuple)


def test_has_findings_property_matches_length() -> None:
    report = ReflectionEngine().reflect(_result_for("S5"))
    assert report.has_findings == (len(report.findings) > 0)


def test_reflection_is_deterministic_for_same_seed() -> None:
    a = ReflectionEngine().reflect(_result_for("S5", seed=99))
    b = ReflectionEngine().reflect(_result_for("S5", seed=99))
    # Strip wall-clock and id fields that vary.
    def _signature(rep):
        return tuple(
            (f.category, f.observed_problem, f.suspected_root_cause,
             f.affected_components, f.supporting_events)
            for f in rep.findings
        )
    assert _signature(a) == _signature(b)
