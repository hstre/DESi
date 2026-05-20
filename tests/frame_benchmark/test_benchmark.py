"""Tests for the v3.4 frame benchmark — Aufgabe 8 + 10."""
from __future__ import annotations

from desi.frame_benchmark import (
    ALL_FRAME_CASES,
    FrameBenchmarkRunner,
    FrameCategory,
    cases_by_category,
    compute_frame_metrics,
)
from desi.frames import FrameKind
from desi.memory.claim import ClaimState


def test_at_least_forty_cases() -> None:
    assert len(ALL_FRAME_CASES) >= 40


def test_each_of_eight_categories_present() -> None:
    for cat in FrameCategory:
        assert len(cases_by_category(cat)) >= 5


def test_all_case_ids_unique() -> None:
    ids = [c.case_id for c in ALL_FRAME_CASES]
    assert len(set(ids)) == len(ids)


def test_every_case_has_required_fields() -> None:
    for c in ALL_FRAME_CASES:
        assert isinstance(c.expected_frame, FrameKind)
        assert isinstance(c.expected_state, ClaimState)
        assert isinstance(c.expected_allowed_pipeline, tuple)
        assert isinstance(c.expected_blocked_pipeline, tuple)


def test_benchmark_runs_to_completion() -> None:
    run = FrameBenchmarkRunner().run()
    assert len(run.results) == len(ALL_FRAME_CASES)


def test_all_cases_resolve_correctly_under_v34() -> None:
    """The shipped detector + cases must agree 40/40."""
    run = FrameBenchmarkRunner().run()
    bad = [r for r in run.results if not r.correct]
    assert not bad, (
        "frame benchmark failures: "
        + ", ".join(
            f"{r.case.case_id} ({r.case.expected_frame.value} vs "
            f"{r.declaration.frame_kind.value})"
            for r in bad[:5]
        )
    )


def test_two_runs_produce_identical_per_case_results() -> None:
    a = FrameBenchmarkRunner().run()
    b = FrameBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.declaration.replay_hash == rb.declaration.replay_hash


def test_metrics_carry_required_fields() -> None:
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    for f in (
        "total", "frame_correct", "state_correct",
        "pipeline_correct", "fully_correct",
        "conflict_rate", "undeclared_rate",
        "pipeline_block_rate", "per_category_correct",
    ):
        assert hasattr(m, f)


def test_undeclared_blocks_promotion() -> None:
    """Aufgabe 4 — FRAME_UNDECLARED yields zero allowed pipelines."""
    from desi.frames import allowed_pipelines
    assert allowed_pipelines(FrameKind.FRAME_UNDECLARED) == ()


def test_conflict_rate_nonzero_in_real_corpus() -> None:
    """At least one case in the v3.4 corpus must surface as a
    conflict so the metric carries signal."""
    m = compute_frame_metrics(FrameBenchmarkRunner().run())
    assert m.conflict_rate > 0
