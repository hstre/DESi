"""Tests for v1.5 case coverage — exactly 50 cases, 10 per category."""
from __future__ import annotations

from desi.benchmark import (
    ALL_CASES,
    Category,
    GroundTruth,
    cases_by_category,
)


# ---------------------------------------------------------------------------
# Total count + per-category count
# ---------------------------------------------------------------------------


def test_total_case_count_is_fifty() -> None:
    assert len(ALL_CASES) == 50


def test_each_category_has_ten_cases() -> None:
    for cat in Category:
        assert len(cases_by_category(cat)) == 10, f"category {cat} miscount"


def test_categories_form_a_closed_set_of_five() -> None:
    assert len(list(Category)) == 5


def test_ground_truths_form_a_closed_set_of_four() -> None:
    assert len(list(GroundTruth)) == 4


# ---------------------------------------------------------------------------
# Case ids are unique and follow the {A..E}{1..10} pattern
# ---------------------------------------------------------------------------


def test_all_case_ids_unique() -> None:
    ids = [c.case_id for c in ALL_CASES]
    assert len(set(ids)) == len(ids)


def test_case_ids_match_category_prefix() -> None:
    prefix_for = {
        Category.A_EVERYDAY_CAUSALITY: "A",
        Category.B_CLASSICAL_LOGIC: "B",
        Category.C_AUTHORITY_TRAPS: "C",
        Category.D_METAPHOR_AMBIGUITY: "D",
        Category.E_PHILOSOPHICAL_STRESS: "E",
    }
    for c in ALL_CASES:
        assert c.case_id.startswith(prefix_for[c.category]), (
            f"case {c.case_id} prefix does not match category {c.category}"
        )


# ---------------------------------------------------------------------------
# Cases are well-formed: non-empty text, non-empty note
# ---------------------------------------------------------------------------


def test_every_case_has_non_empty_text() -> None:
    for c in ALL_CASES:
        assert c.text.strip(), f"case {c.case_id} has empty text"


def test_every_case_has_a_note() -> None:
    """The note documents the case's epistemic premise — the benchmark
    is a research instrument, not a fixture pool."""
    for c in ALL_CASES:
        assert c.note.strip(), f"case {c.case_id} has no note"


# ---------------------------------------------------------------------------
# Category-specific contracts
# ---------------------------------------------------------------------------


def test_category_b_has_at_least_one_should_reject() -> None:
    cats = cases_by_category(Category.B_CLASSICAL_LOGIC)
    assert any(c.ground_truth is GroundTruth.SHOULD_REJECT for c in cats), (
        "Category B must contain at least one explicit-invalid-inference "
        "case (SHOULD_REJECT)."
    )


def test_category_c_is_entirely_should_block() -> None:
    """Authority cases must never be marked SHOULD_RESOLVE."""
    cats = cases_by_category(Category.C_AUTHORITY_TRAPS)
    for c in cats:
        assert c.ground_truth is GroundTruth.SHOULD_BLOCK, (
            f"authority case {c.case_id} carries non-block ground truth"
        )


def test_category_d_contains_no_should_resolve() -> None:
    """Metaphors must never be ground-truthed as SHOULD_RESOLVE."""
    cats = cases_by_category(Category.D_METAPHOR_AMBIGUITY)
    for c in cats:
        assert c.ground_truth is not GroundTruth.SHOULD_RESOLVE


def test_category_e_contains_no_should_resolve() -> None:
    """Philosophical cases must never be ground-truthed as
    SHOULD_RESOLVE. DESi must never hallucinate certainty here."""
    cats = cases_by_category(Category.E_PHILOSOPHICAL_STRESS)
    for c in cats:
        assert c.ground_truth is not GroundTruth.SHOULD_RESOLVE


# ---------------------------------------------------------------------------
# case_by_id lookup
# ---------------------------------------------------------------------------


def test_case_by_id_returns_the_right_case() -> None:
    from desi.benchmark import case_by_id
    c = case_by_id("B1")
    assert c.category is Category.B_CLASSICAL_LOGIC
    assert c.ground_truth is GroundTruth.SHOULD_RESOLVE


def test_case_by_id_rejects_unknown_id() -> None:
    import pytest
    from desi.benchmark import case_by_id
    with pytest.raises(KeyError):
        case_by_id("Z99")
