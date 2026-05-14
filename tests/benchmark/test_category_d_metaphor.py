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


def test_category_d_pinned_blocked_count_is_nine() -> None:
    """9 of 10 metaphor cases correctly block at depth 0.

    Documented finding: the resolver blocks because v1.2's premise
    extractor returns NO_EXPLICIT_CHAIN for sentences without an
    explicit 'Therefore'.
    """
    run = _cat_d_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 9


def test_category_d_pinned_false_positive_count_is_one() -> None:
    """D3 silently completes despite the financial-newspaper context.

    Documented finding: v1.4 does not thread the case's `context`
    field into the consilium (the v1.3 DOMAIN_EXAMINER's metaphor
    library is reachable only via direct
    BridgeConsilium.deliberate(context=...) calls). v1.6+ should
    pipe the context through the resolver.
    """
    run = _cat_d_run()
    fps = sum(1 for r in run.results if r.false_positive)
    assert fps == 1


def test_d3_is_the_known_metaphor_silent_completion() -> None:
    run = BenchmarkRunner().run((case_by_id("D3"),))
    r = run.results[0]
    assert r.case.context == "financial_newspaper"
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.false_positive is True
