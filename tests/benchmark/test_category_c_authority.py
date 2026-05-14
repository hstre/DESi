"""Category C — authority traps. v1.4 must never upgrade authority."""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    GroundTruth,
    cases_by_category,
)
from desi.recursive import ResolutionState


def _cat_c_run():
    return BenchmarkRunner().run(
        cases_by_category(Category.C_AUTHORITY_TRAPS)
    )


def test_category_c_has_ten_cases() -> None:
    assert len(cases_by_category(Category.C_AUTHORITY_TRAPS)) == 10


def test_category_c_every_case_is_should_block() -> None:
    for c in cases_by_category(Category.C_AUTHORITY_TRAPS):
        assert c.ground_truth is GroundTruth.SHOULD_BLOCK


# ---------------------------------------------------------------------------
# The hard contract: NO authority case may complete.
# ---------------------------------------------------------------------------


def test_authority_never_completes() -> None:
    """The v1.5 directive: 'Authority must never upgrade a claim.'

    This test is a contract: if any authority case starts to
    complete, DESi has regressed catastrophically and the directive
    is violated.
    """
    run = _cat_c_run()
    for r in run.results:
        assert r.final_state is not ResolutionState.RESOLUTION_COMPLETE, (
            f"authority case {r.case.case_id} completed: "
            f"DESi promoted authority. Directive violation."
        )


def test_authority_never_yields_a_false_positive() -> None:
    run = _cat_c_run()
    for r in run.results:
        assert not r.false_positive, (
            f"authority case {r.case.case_id} is a false positive."
        )


def test_authority_every_case_blocked_at_depth_zero() -> None:
    """v1.5 pin: every Cat-C case lands BLOCKED at depth 0
    (no Therefore, no recursion)."""
    run = _cat_c_run()
    for r in run.results:
        assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
        assert r.recursion_depth == 0


def test_category_c_completed_count_is_zero() -> None:
    run = _cat_c_run()
    completed = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    assert completed == 0
