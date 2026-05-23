"""Tests for v0.8 ScenarioAggregate — mean / median / std correctness."""
from __future__ import annotations

import statistics

from desi.evolution import MetricsDelta, PathQualityMetrics, ScenarioAggregate
from desi.evolution.multi_seed import _aggregate_one_scenario
from desi.evolution.paired_evaluation import PairedScenarioOutcome


def _outcome(
    scenario_id: str,
    branch_delta: int,
    timeline_delta: int = 0,
    guard_delta: int = 0,
) -> PairedScenarioOutcome:
    """Build a paired outcome with a chosen set of deltas."""
    stable = PathQualityMetrics(
        scenario_id=scenario_id,
        timeline_length=27,
        branch_opened_count=4,
        guard_blocked_count=2,
        contradicts_count=0,
        merged_into_count=0,
        hook_error_count=0,
    )
    clone = PathQualityMetrics(
        scenario_id=scenario_id,
        timeline_length=27 + timeline_delta,
        branch_opened_count=4 + branch_delta,
        guard_blocked_count=2 + guard_delta,
        contradicts_count=0,
        merged_into_count=0,
        hook_error_count=0,
    )
    return PairedScenarioOutcome(
        scenario_id=scenario_id,
        stable_result=None,    # type: ignore
        clone_result=None,     # type: ignore
        stable_metrics=stable,
        clone_metrics=clone,
        delta=MetricsDelta(stable=stable, clone=clone),
    )


# ---------------------------------------------------------------------------
# Mean
# ---------------------------------------------------------------------------


def test_mean_branch_delta_matches_statistics_fmean() -> None:
    deltas = [-1, -2, 0, -1, -1]
    outcomes = [_outcome("X", d) for d in deltas]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.mean_branch_delta == statistics.fmean(deltas)


def test_mean_is_zero_when_all_deltas_are_zero() -> None:
    outcomes = [_outcome("X", 0) for _ in range(5)]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.mean_branch_delta == 0.0


# ---------------------------------------------------------------------------
# Median
# ---------------------------------------------------------------------------


def test_median_branch_delta_matches_statistics_median() -> None:
    deltas = [-2, -1, -1, 0, +1]
    outcomes = [_outcome("X", d) for d in deltas]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.median_branch_delta == statistics.median(deltas)


def test_median_of_odd_set_is_middle_value() -> None:
    outcomes = [_outcome("X", d) for d in [-3, -1, 0]]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.median_branch_delta == -1


# ---------------------------------------------------------------------------
# Population std
# ---------------------------------------------------------------------------


def test_std_branch_delta_matches_statistics_pstdev() -> None:
    deltas = [-1, -2, 0, -1, -1]
    outcomes = [_outcome("X", d) for d in deltas]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.std_branch_delta == statistics.pstdev(deltas)


def test_std_is_zero_for_constant_deltas() -> None:
    outcomes = [_outcome("X", -1) for _ in range(5)]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.std_branch_delta == 0.0


def test_std_is_zero_for_single_sample() -> None:
    """Population std of n=1 must not raise. Returns 0.0."""
    outcomes = [_outcome("X", -1)]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.std_branch_delta == 0.0


# ---------------------------------------------------------------------------
# Verdict tallies
# ---------------------------------------------------------------------------


def test_aggregate_counts_improved_neutral_regressed_per_seed() -> None:
    # In v0.7 verdict semantics, a branch_delta=-1 alone is "regressed"
    # because the timeline delta is unexplained. The mechanism-correct
    # improvement pattern is branch_delta=-1 with guard_delta=+1 (the
    # BRANCH_OPENED→GUARD_BLOCKED swap), which nets the timeline to 0.
    outcomes = [
        _outcome("X", branch_delta=-1, guard_delta=+1),  # improved
        _outcome("X", branch_delta=-1, guard_delta=+1),  # improved
        _outcome("X", 0),                                # neutral
        _outcome("X", branch_delta=-1, guard_delta=+1),  # improved
        _outcome("X", branch_delta=-1, guard_delta=+1),  # improved
    ]
    agg = _aggregate_one_scenario("X", outcomes)
    assert agg.improved_seed_count == 4
    assert agg.neutral_seed_count == 1
    assert agg.regressed_seed_count == 0


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def test_to_dict_includes_all_aggregate_fields() -> None:
    outcomes = [_outcome("X", -1) for _ in range(5)]
    agg = _aggregate_one_scenario("X", outcomes)
    d = agg.to_dict()
    for k in (
        "scenario_id", "n_seeds",
        "mean_branch_delta", "median_branch_delta", "std_branch_delta",
        "mean_timeline_delta", "median_timeline_delta", "std_timeline_delta",
        "mean_guard_delta",
        "per_seed_verdicts",
        "improved_seed_count", "neutral_seed_count", "regressed_seed_count",
    ):
        assert k in d, f"missing key in aggregate dict: {k}"
