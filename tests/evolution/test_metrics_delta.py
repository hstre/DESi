"""Tests for MetricsDelta — verdict computation."""
from __future__ import annotations

from desi.evolution import MetricsDelta, PathQualityMetrics


def _metrics(**overrides) -> PathQualityMetrics:
    base = dict(
        scenario_id="S2",
        timeline_length=25,
        branch_opened_count=3,
        guard_blocked_count=0,
        contradicts_count=2,
        merged_into_count=0,
        hook_error_count=0,
    )
    base.update(overrides)
    return PathQualityMetrics(**base)


# ---------------------------------------------------------------------------
# Absolute deltas
# ---------------------------------------------------------------------------


def test_delta_is_zero_when_stable_equals_clone() -> None:
    a = _metrics()
    d = MetricsDelta(stable=a, clone=a)
    assert d.timeline_length_delta == 0
    assert d.branch_opened_delta == 0
    assert d.guard_blocked_delta == 0
    assert d.contradicts_delta == 0
    assert d.merged_into_delta == 0
    assert d.hook_error_delta == 0


def test_delta_branch_reduction() -> None:
    stable = _metrics(branch_opened_count=4, guard_blocked_count=2)
    clone = _metrics(branch_opened_count=3, guard_blocked_count=3)
    d = MetricsDelta(stable=stable, clone=clone)
    assert d.branch_opened_delta == -1
    assert d.guard_blocked_delta == +1


def test_branch_reduction_pct() -> None:
    stable = _metrics(branch_opened_count=4)
    clone = _metrics(branch_opened_count=3)
    d = MetricsDelta(stable=stable, clone=clone)
    assert d.branch_reduction_pct == 25.0  # (4-3)/4 * 100


def test_branch_reduction_pct_is_zero_when_stable_is_zero() -> None:
    stable = _metrics(branch_opened_count=0)
    clone = _metrics(branch_opened_count=0)
    d = MetricsDelta(stable=stable, clone=clone)
    assert d.branch_reduction_pct == 0.0


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def test_verdict_neutral_when_everything_matches() -> None:
    a = _metrics()
    assert MetricsDelta(stable=a, clone=a).verdict == "neutral"


def test_verdict_improved_when_branches_reduce_and_others_neutral() -> None:
    # Branch suppression in v0.7 also emits guard_blocked events.
    # The verdict treats the swap as net-zero on timeline / event count.
    stable = _metrics(branch_opened_count=4, guard_blocked_count=2,
                      timeline_length=27)
    clone = _metrics(branch_opened_count=3, guard_blocked_count=3,
                     timeline_length=27)
    assert MetricsDelta(stable=stable, clone=clone).verdict == "improved"


def test_verdict_regressed_when_more_branches_open() -> None:
    stable = _metrics(branch_opened_count=3)
    clone = _metrics(branch_opened_count=4)
    assert MetricsDelta(stable=stable, clone=clone).verdict == "regressed"


def test_verdict_regressed_when_contradicts_count_drifts() -> None:
    stable = _metrics(contradicts_count=2)
    clone = _metrics(contradicts_count=0)  # CONTRADICTS detection lost
    assert MetricsDelta(stable=stable, clone=clone).verdict == "regressed"


def test_verdict_regressed_when_merged_into_count_drifts() -> None:
    stable = _metrics(merged_into_count=0)
    clone = _metrics(merged_into_count=1)  # false merge introduced
    assert MetricsDelta(stable=stable, clone=clone).verdict == "regressed"


def test_verdict_regressed_when_hook_errors_increase() -> None:
    stable = _metrics(hook_error_count=0)
    clone = _metrics(hook_error_count=1)
    assert MetricsDelta(stable=stable, clone=clone).verdict == "regressed"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_delta_is_deterministic_given_identical_metrics() -> None:
    a = _metrics()
    b = _metrics(branch_opened_count=4)
    d1 = MetricsDelta(stable=a, clone=b)
    d2 = MetricsDelta(stable=a, clone=b)
    assert d1 == d2
    assert d1.verdict == d2.verdict


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def test_to_dict_includes_absolute_relative_and_verdict() -> None:
    stable = _metrics(branch_opened_count=4)
    clone = _metrics(branch_opened_count=3)
    d = MetricsDelta(stable=stable, clone=clone).to_dict()
    assert d["scenario_id"] == "S2"
    assert "absolute" in d
    assert "relative" in d
    assert d["absolute"]["branch_opened_delta"] == -1
    assert d["relative"]["branch_reduction_pct"] == 25.0
    assert d["verdict"] in {"improved", "neutral", "regressed"}
