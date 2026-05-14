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


def test_category_e_pinned_blocked_count_is_seven() -> None:
    run = _cat_e_run()
    blocked = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED
    )
    assert blocked == 7


def test_category_e_pinned_false_positive_count_is_three() -> None:
    """Documented finding: E4, E5, E10 silently complete.

    These are the philosophical cases whose 'Premise. Therefore X.'
    structure produces a clean particular-vs-particular form. The
    auditor proposes a generic bridge; the consilium has no
    counter-evidence; the resolver completes at depth 1. DESi
    invented certainty on three philosophical leaps.
    """
    run = _cat_e_run()
    fps = sum(1 for r in run.results if r.false_positive)
    assert fps == 3


def test_questions_block_correctly() -> None:
    """E1, E2, E3, E6, E7, E8, E9 — questions / definitional claims
    / conditionals without Therefore — all block at depth 0."""
    for case_id in ("E1", "E2", "E3", "E6", "E7", "E8", "E9"):
        run = BenchmarkRunner().run((case_by_id(case_id),))
        r = run.results[0]
        assert r.final_state is ResolutionState.RESOLUTION_BLOCKED, case_id


def test_e10_first_cause_argument_is_a_known_false_positive() -> None:
    """E10: the cosmological argument silently completes — the
    benchmark's single most uncomfortable finding. v1.5 does not
    patch it; v1.6+ must surface adversarial conditions for these
    leaps."""
    run = BenchmarkRunner().run((case_by_id("E10"),))
    r = run.results[0]
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.false_positive is True
