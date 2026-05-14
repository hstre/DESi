"""Category A — everyday causality. Documents v1.4's observed behaviour.

Pinning is intentional: these tests document the v1.5 baseline so
any drift surfaces in CI. v1.6+ may improve the numbers, but it
must update the pinned counts and surface the improvement in the
benchmark report.
"""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    GroundTruth,
    cases_by_category,
    compute_metrics,
)
from desi.recursive import ResolutionState


def _cat_a_run():
    return BenchmarkRunner().run(
        cases_by_category(Category.A_EVERYDAY_CAUSALITY)
    )


def test_category_a_has_ten_cases() -> None:
    assert len(cases_by_category(Category.A_EVERYDAY_CAUSALITY)) == 10


def test_category_a_every_case_ground_truth_is_bridge() -> None:
    for c in cases_by_category(Category.A_EVERYDAY_CAUSALITY):
        assert c.ground_truth is GroundTruth.SHOULD_BRIDGE


def test_category_a_pinned_completion_count() -> None:
    """v1.6 baseline: 0 of 10 causal claims complete.

    v1.5 had 4 silent completions (A5, A6, A7, A10) where a clean
    particular structure produced a generic-fallback bridge that
    the consilium silently accepted. v1.6 kills that loophole:
    GENERIC_FALLBACK bridges with no causal-mechanism word fail
    the LOGICIAN, and the SKEPTIC auto-VETOs them.
    """
    run = _cat_a_run()
    completed = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert completed == 0


def test_category_a_pinned_blocked_count() -> None:
    """v1.6 baseline: all 10 causal claims block.

    Four of these (A5, A6, A7, A10) block via the new v1.6
    generic-fallback gate (LOGICIAN + SKEPTIC). The other six
    still block via the v1.2 premise extractor's narrow
    PARTICULAR pattern — block-by-accident, documented in v1.5
    for v1.7+ work.
    """
    run = _cat_a_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 10


def test_category_a_false_positive_count_is_zero() -> None:
    """v1.6 pin: 0 cases invent certainty (down from 4 in v1.5).

    The dominant failure mode — silent generic-bridge acceptance —
    is gone for Cat A.
    """
    run = _cat_a_run()
    fps = sum(1 for r in run.results if r.false_positive)
    assert fps == 0
