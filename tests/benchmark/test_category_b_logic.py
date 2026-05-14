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
    """v1.6 baseline: 8 of 9 SHOULD_RESOLVE cases complete.

    Same TP count as v1.5 but via a different mechanism for B2,
    B7, B8: those used to complete via generic-fallback bridges
    that the v1.6 consilium would now veto. v1.6 adds the regular
    plural inflections (philosophers/philosopher, cats/cat,
    mammals/mammal, squares/square, rectangles/rectangle) so the
    SYLLOGISM rule matches at the audit level — depth 0, no
    bridge needed. B10 (universal-conclusion syllogism) remains
    the lone FN; addressing it requires a new rule, which v1.6
    deliberately does not add.
    """
    run = _cat_b_run()
    tp = sum(
        1 for r in run.results
        if r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
        and r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert tp == 8


def test_category_b_invalid_transitivity_is_rejected() -> None:
    """B6: a -> b. b -> c. Therefore a -> d. → REJECTED."""
    run = BenchmarkRunner().run((case_by_id("B6"),))
    assert run.results[0].final_state is ResolutionState.RESOLUTION_BLOCKED


def test_category_b10_is_a_known_false_negative() -> None:
    """B10: universal-conclusion syllogism is logically valid but
    sits outside v1.2's Barbara form. Pinned as FN until the rule
    set grows."""
    run = BenchmarkRunner().run((case_by_id("B10"),))
    r = run.results[0]
    assert r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
    assert r.final_state is not ResolutionState.RESOLUTION_COMPLETE
    assert r.false_negative is True


def test_category_b_completed_count_is_pinned_at_eight() -> None:
    run = _cat_b_run()
    completed = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert completed == 8


def test_category_b_blocked_count_is_two() -> None:
    """B6 (correctly rejected) + B10 (false-negative reject)."""
    run = _cat_b_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 2


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
