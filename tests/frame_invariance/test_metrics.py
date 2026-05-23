"""Tests for v3.5 invariance metrics (Aufgaben 4 + 8)."""
from __future__ import annotations

from desi.frame_invariance import (
    FrameInvarianceRunner,
    compute_invariance_metrics,
    strongest_frame,
    weakest_frame,
)


def test_metrics_carry_required_fields() -> None:
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    for f in (
        "total_cases", "total_groups",
        "frame_accuracy", "group_invariance_rate",
        "conflict_rate", "undeclared_rate",
        "forbidden_frame_hit_rate",
        "per_frame_accuracy", "per_frame_invariance",
        "failure_distribution",
    ):
        assert hasattr(m, f)


def test_total_cases_matches_run() -> None:
    run = FrameInvarianceRunner().run()
    m = compute_invariance_metrics(run)
    assert m.total_cases == len(run.results)


def test_total_groups_equals_eighty() -> None:
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    assert m.total_groups == 80


def test_rates_in_unit_interval() -> None:
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    for r in (
        m.frame_accuracy, m.group_invariance_rate,
        m.conflict_rate, m.undeclared_rate,
        m.forbidden_frame_hit_rate,
    ):
        assert 0.0 <= r <= 1.0


def test_metrics_deterministic_across_two_runs() -> None:
    a = compute_invariance_metrics(FrameInvarianceRunner().run())
    b = compute_invariance_metrics(FrameInvarianceRunner().run())
    assert a.to_dict() == b.to_dict()


def test_per_frame_accuracy_covers_seven_frames() -> None:
    """At least the 7 declarable frames appear (FRAME_UNDECLARED
    is not an 'expected' frame in any group)."""
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    assert len(m.per_frame_accuracy) == 8


def test_forbidden_frame_hit_rate_is_zero_in_v35_corpus() -> None:
    """The v3.5 corpus is designed so paraphrases never hit a
    forbidden frame. If this regresses, a forbidden-frame guard
    has slipped."""
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    assert m.forbidden_frame_hit_rate == 0.0


def test_weakest_and_strongest_frame_are_strings() -> None:
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    w = weakest_frame(m)
    s = strongest_frame(m)
    assert isinstance(w[0], str) and 0.0 <= w[1] <= 1.0
    assert isinstance(s[0], str) and 0.0 <= s[1] <= 1.0
    assert s[1] >= w[1]


def test_frame_accuracy_above_eight_tenths() -> None:
    """Sanity floor: the detector is strong enough on the v3.5
    corpus that the paraphrase audit hits >= 80% per-case
    accuracy. A drop below this should fail-closed."""
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    assert m.frame_accuracy >= 0.80, (
        f"frame_accuracy = {m.frame_accuracy}"
    )


def test_group_invariance_rate_above_eight_tenths() -> None:
    m = compute_invariance_metrics(FrameInvarianceRunner().run())
    assert m.group_invariance_rate >= 0.80
