"""Tests for v2.3 multi-step metrics (Aufgabe 4)."""
from __future__ import annotations

from desi.benchmark_multistep import (
    MultiStepBenchmarkRunner,
    compute_multistep_metrics,
)


def test_metrics_carry_five_named_observables() -> None:
    run = MultiStepBenchmarkRunner().run()
    m = compute_multistep_metrics(run)
    for f in (
        "recursion_usage_rate", "mean_depth_when_complete",
        "false_depth_zero_rate", "cycle_detection_rate",
        "blocked_propagation_accuracy",
    ):
        assert hasattr(m, f)


def test_recursion_usage_rate_is_unit_interval() -> None:
    m = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    assert 0.0 <= m.recursion_usage_rate <= 1.0


def test_false_depth_zero_rate_is_unit_interval() -> None:
    m = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    assert 0.0 <= m.false_depth_zero_rate <= 1.0


def test_cycle_detection_rate_is_unit_interval() -> None:
    m = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    assert 0.0 <= m.cycle_detection_rate <= 1.0


def test_blocked_propagation_accuracy_is_unit_interval() -> None:
    m = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    assert 0.0 <= m.blocked_propagation_accuracy <= 1.0


def test_metrics_are_deterministic() -> None:
    a = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    b = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    assert a.recursion_usage_rate == b.recursion_usage_rate
    assert a.mean_depth_when_complete == b.mean_depth_when_complete
    assert a.false_depth_zero_rate == b.false_depth_zero_rate
    assert a.cycle_detection_rate == b.cycle_detection_rate
    assert a.blocked_propagation_accuracy == b.blocked_propagation_accuracy


def test_depth_histogram_counts_sum_to_total() -> None:
    m = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    counted = sum(c for _, c in m.depth_histogram)
    assert counted == m.total


def test_per_category_correct_covers_all_five_categories() -> None:
    m = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    cats = {row[0] for row in m.per_category_correct}
    assert len(cats) == 5


def test_to_dict_shape() -> None:
    m = compute_multistep_metrics(MultiStepBenchmarkRunner().run())
    d = m.to_dict()
    for k in (
        "total", "recursion_usage_rate", "mean_depth_when_complete",
        "false_depth_zero_rate", "cycle_detection_rate",
        "blocked_propagation_accuracy", "depth_histogram",
        "per_category_correct",
    ):
        assert k in d
