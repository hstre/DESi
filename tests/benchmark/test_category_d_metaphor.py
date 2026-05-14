"""Category D — metaphor / ambiguity. Pinned at v1.5 baseline."""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    case_by_id,
    cases_by_category,
)
from desi.recursive import ResolutionState


def _cat_d_run():
    return BenchmarkRunner().run(
        cases_by_category(Category.D_METAPHOR_AMBIGUITY)
    )


def test_category_d_has_ten_cases() -> None:
    assert len(cases_by_category(Category.D_METAPHOR_AMBIGUITY)) == 10


def test_category_d_pinned_blocked_count_is_ten() -> None:
    """v1.6 baseline: all 10 metaphor cases correctly block.

    Nine were blocked in v1.5 (no explicit chain). The tenth (D3,
    financial-context metaphor) now blocks because v1.6 threads
    the case's ``context`` into the consilium, where the
    DOMAIN_EXAMINER's metaphor library flags 'flooded' as
    ambiguous and the SKEPTIC auto-VETOs the generic bridge.
    """
    run = _cat_d_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 10


def test_category_d_pinned_false_positive_count_is_zero() -> None:
    """v1.6 pin: zero FP in Category D (down from 1 in v1.5).

    D3's silent completion was the v1.5 directive's smoking gun
    for context threading. v1.6 fixes it.
    """
    run = _cat_d_run()
    fps = sum(1 for r in run.results if r.false_positive)
    assert fps == 0


def test_d3_metaphor_now_blocks_under_context_threading() -> None:
    """D3 (financial newspaper + 'flooded') was the v1.5 silent
    completion. v1.6 threads the case's context into the consilium,
    the DOMAIN_EXAMINER flags the metaphor, and the SKEPTIC's
    GENERIC_FALLBACK gate independently vetoes the bridge."""
    run = BenchmarkRunner().run((case_by_id("D3"),))
    r = run.results[0]
    assert r.case.context == "financial_newspaper"
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.false_positive is False
