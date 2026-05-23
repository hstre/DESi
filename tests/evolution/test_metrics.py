"""Tests for PathQualityMetrics — deterministic raw counters."""
from __future__ import annotations

import pytest

from desi.eval import EvaluationHarness, scenario_by_id
from desi.evolution import PathQualityMetrics, compute_path_quality


def _result(scenario_id: str, seed: int = 42):
    harness = EvaluationHarness(model="m")
    return harness.run_scenario(scenario_by_id(scenario_id), seed=seed)


def test_metrics_fields_are_integers() -> None:
    m = compute_path_quality(_result("S2"))
    assert isinstance(m, PathQualityMetrics)
    assert isinstance(m.timeline_length, int)
    assert isinstance(m.branch_opened_count, int)
    assert isinstance(m.guard_blocked_count, int)
    assert isinstance(m.contradicts_count, int)
    assert isinstance(m.merged_into_count, int)
    assert isinstance(m.hook_error_count, int)


def test_metrics_carry_scenario_id() -> None:
    m = compute_path_quality(_result("S6"))
    assert m.scenario_id == "S6"


def test_metrics_are_deterministic_across_runs() -> None:
    a = compute_path_quality(_result("S2", seed=11))
    b = compute_path_quality(_result("S2", seed=11))
    assert a == b


def test_s2_has_at_least_two_contradicts_edges() -> None:
    m = compute_path_quality(_result("S2"))
    assert m.contradicts_count >= 2  # bidirectional CONTRADICTS


def test_s6_has_at_least_one_guard_blocked_and_no_merged_into() -> None:
    m = compute_path_quality(_result("S6"))
    assert m.guard_blocked_count >= 1
    assert m.merged_into_count == 0


def test_metrics_to_dict_round_trip() -> None:
    m = compute_path_quality(_result("S2"))
    d = m.to_dict()
    assert d["scenario_id"] == "S2"
    assert d["timeline_length"] == m.timeline_length
    assert d["contradicts_count"] == m.contradicts_count
