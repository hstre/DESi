"""Tests for benchmark metrics — precision / recall / rates / averages."""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkMetrics,
    BenchmarkRunner,
    Category,
    GroundTruth,
    compute_metrics,
)
from desi.recursive import ResolutionState


def _run():
    return BenchmarkRunner().run()


# ---------------------------------------------------------------------------
# Output shape
# ---------------------------------------------------------------------------


def test_compute_metrics_returns_benchmark_metrics() -> None:
    m = compute_metrics(_run())
    assert isinstance(m, BenchmarkMetrics)


def test_metrics_carries_expected_fields() -> None:
    m = compute_metrics(_run())
    for f in ("total", "positive_truth", "positive_predicted",
              "true_positives", "false_positives", "false_negatives",
              "true_negatives", "precision", "recall",
              "overblocking_rate", "unjustified_acceptance_rate",
              "avg_bridge_depth", "avg_recursion_depth",
              "per_category"):
        assert hasattr(m, f), f"missing metrics field: {f}"


def test_metrics_total_matches_run_size() -> None:
    m = compute_metrics(_run())
    assert m.total == 50


# ---------------------------------------------------------------------------
# Arithmetic identities (TP + FP + FN + TN == total)
# ---------------------------------------------------------------------------


def test_confusion_matrix_partitions_the_run() -> None:
    m = compute_metrics(_run())
    assert (m.true_positives + m.false_positives
            + m.false_negatives + m.true_negatives) == m.total


def test_precision_lies_in_unit_interval() -> None:
    m = compute_metrics(_run())
    assert 0.0 <= m.precision <= 1.0


def test_recall_lies_in_unit_interval() -> None:
    m = compute_metrics(_run())
    assert 0.0 <= m.recall <= 1.0


def test_overblocking_rate_lies_in_unit_interval() -> None:
    m = compute_metrics(_run())
    assert 0.0 <= m.overblocking_rate <= 1.0


def test_unjustified_acceptance_rate_lies_in_unit_interval() -> None:
    m = compute_metrics(_run())
    assert 0.0 <= m.unjustified_acceptance_rate <= 1.0


# ---------------------------------------------------------------------------
# Per-category totals partition the run
# ---------------------------------------------------------------------------


def test_per_category_totals_sum_to_overall_total() -> None:
    m = compute_metrics(_run())
    assert sum(c.total for c in m.per_category) == 50


def test_per_category_is_indexed_by_all_five_categories() -> None:
    m = compute_metrics(_run())
    cats = {c.category for c in m.per_category}
    assert cats == set(Category)


def test_per_category_completed_plus_blocked_etc_equals_total() -> None:
    m = compute_metrics(_run())
    for cm in m.per_category:
        assert (cm.completed + cm.blocked + cm.cycle
                + cm.depth_exceeded) == cm.total


# ---------------------------------------------------------------------------
# Category C (authority) must have zero completions and zero false-positives
# ---------------------------------------------------------------------------


def test_category_c_authority_never_completes() -> None:
    """The directive's hard contract: authority must never upgrade."""
    m = compute_metrics(_run())
    for cm in m.per_category:
        if cm.category is Category.C_AUTHORITY_TRAPS:
            assert cm.completed == 0
            assert cm.false_positives == 0


# ---------------------------------------------------------------------------
# Sanity: TPs are exactly the cases that both should_resolve AND completed.
# ---------------------------------------------------------------------------


def test_true_positives_match_should_resolve_and_completed() -> None:
    run = _run()
    expected = sum(
        1 for r in run.results
        if r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
        and r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    m = compute_metrics(run)
    assert m.true_positives == expected
