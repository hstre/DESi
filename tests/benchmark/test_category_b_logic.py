"""Category B — classical logic. Documents v1.4's observed behaviour."""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    GroundTruth,
    case_by_id,
    cases_by_category,
)
from desi.recursive import ResolutionState


def _cat_b_run():
    return BenchmarkRunner().run(
        cases_by_category(Category.B_CLASSICAL_LOGIC)
    )


def test_category_b_has_ten_cases() -> None:
    assert len(cases_by_category(Category.B_CLASSICAL_LOGIC)) == 10


def test_category_b_pinned_true_positive_count() -> None:
    """v1.7 baseline: 9 of 9 SHOULD_RESOLVE cases complete.

    v1.7 closes the last Cat-B false negative (B10) by extending
    the existing SYLLOGISM rule with a universal-conclusion form:
    "All A are B. All B are C. Therefore all A are C." Same rule,
    new branch — no new operator, no new heuristic.
    """
    run = _cat_b_run()
    tp = sum(
        1 for r in run.results
        if r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
        and r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert tp == 9


def test_category_b_invalid_transitivity_is_rejected() -> None:
    """B6: a -> b. b -> c. Therefore a -> d. → REJECTED."""
    run = BenchmarkRunner().run((case_by_id("B6"),))
    assert run.results[0].final_state is ResolutionState.RESOLUTION_BLOCKED


def test_category_b10_universal_conclusion_now_completes() -> None:
    """v1.7: B10 ("All A are B. All B are C. Therefore all A are C.")
    completes via the universal-conclusion branch of the SYLLOGISM
    rule. No new operator: same `try_each_rule` orchestration, same
    closed inference enum — only the syllogism rule's conclusion
    shape was widened.
    """
    run = BenchmarkRunner().run((case_by_id("B10"),))
    r = run.results[0]
    assert r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.false_negative is False


def test_category_b_completed_count_is_pinned_at_nine() -> None:
    """v1.7: nine completions, up from eight in v1.6 — B10 joins."""
    run = _cat_b_run()
    completed = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert completed == 9


def test_category_b_blocked_count_is_one() -> None:
    """v1.7: only B6 (correctly rejected invalid transitivity)
    remains blocked in Category B."""
    run = _cat_b_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 1


def test_category_b_canonical_syllogism_completes_at_depth_zero() -> None:
    """B1 must hit the SYLLOGISM inference rule directly — no
    bridges, no recursion."""
    run = BenchmarkRunner().run((case_by_id("B1"),))
    r = run.results[0]
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.recursion_depth == 0
    assert r.bridge_count == 0


def test_v16_inflection_aware_syllogisms_complete_at_depth_zero() -> None:
    """v1.6: B2, B7, B8 must now hit the SYLLOGISM rule directly,
    no longer falling through to the generic-fallback bridge."""
    for cid in ("B2", "B7", "B8"):
        run = BenchmarkRunner().run((case_by_id(cid),))
        r = run.results[0]
        assert r.final_state is ResolutionState.RESOLUTION_COMPLETE, cid
        assert r.recursion_depth == 0, (
            f"{cid} resolved at depth {r.recursion_depth}; expected "
            f"depth=0 after v1.6 inflection-aware syllogism."
        )
