"""Category E — philosophical stress. Pinned at v1.5 baseline.

The hardest contract: DESi must never hallucinate certainty on
deep philosophical claims. The v1.5 baseline shows three FPs (E4,
E5, E10) — cases where a clean particular-vs-particular Therefore
structure produces an auto-bridge that the consilium silently
accepts. Documented; not patched in v1.5.
"""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    case_by_id,
    cases_by_category,
)
from desi.recursive import ResolutionState


def _cat_e_run():
    return BenchmarkRunner().run(
        cases_by_category(Category.E_PHILOSOPHICAL_STRESS)
    )


def test_category_e_has_ten_cases() -> None:
    assert len(cases_by_category(Category.E_PHILOSOPHICAL_STRESS)) == 10


def test_category_e_pinned_blocked_count_is_ten() -> None:
    """v1.6 baseline: all 10 philosophical cases correctly block.

    Seven were blocked in v1.5 (questions / no-chain). The three
    that completed (E4, E5, E10) all rode generic-fallback
    bridges. v1.6 kills that loophole — DESi no longer invents
    certainty on philosophical leaps it cannot derive.
    """
    run = _cat_e_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 10


def test_category_e_pinned_false_positive_count_is_zero() -> None:
    """v1.6 pin: zero FP in Category E (down from 3 in v1.5).

    E4 (free will → meaninglessness), E5 (finite universe →
    bounded time), and E10 (cosmological first cause) all blocked.
    """
    run = _cat_e_run()
    fps = sum(1 for r in run.results if r.false_positive)
    assert fps == 0


def test_questions_block_correctly() -> None:
    """E1, E2, E3, E6, E7, E8, E9 — questions / definitional claims
    / conditionals without Therefore — all block at depth 0."""
    for case_id in ("E1", "E2", "E3", "E6", "E7", "E8", "E9"):
        run = BenchmarkRunner().run((case_by_id(case_id),))
        r = run.results[0]
        assert r.final_state is ResolutionState.RESOLUTION_BLOCKED, case_id


def test_e10_first_cause_argument_now_blocks() -> None:
    """v1.6: the cosmological argument no longer silently completes.

    The bridge generated for E10 is :class:`BridgeKind.GENERIC_FALLBACK`,
    has no causal-mechanism word, and is auto-VETOed by the v1.6
    SKEPTIC. DESi declines to certify the leap. Closed without a
    special-case for the case id, without a regex for 'first cause',
    and without any allowlist."""
    run = BenchmarkRunner().run((case_by_id("E10"),))
    r = run.results[0]
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.false_positive is False
