"""Tests for v2.3 multi-step case schema (Aufgaben 1, 2)."""
from __future__ import annotations

from desi.benchmark_multistep import (
    ALL_MULTISTEP_CASES,
    MultiStepCategory,
    R1_CASES, R2_CASES, R3_CASES, R4_CASES, R5_CASES,
    cases_by_category,
)
from desi.recursive import ResolutionState


def test_thirty_cases_exactly() -> None:
    assert len(ALL_MULTISTEP_CASES) == 30


def test_each_category_has_six_cases() -> None:
    for cat in MultiStepCategory:
        assert len(cases_by_category(cat)) == 6


def test_category_partitions() -> None:
    assert len(R1_CASES) == 6
    assert len(R2_CASES) == 6
    assert len(R3_CASES) == 6
    assert len(R4_CASES) == 6
    assert len(R5_CASES) == 6


def test_case_ids_unique() -> None:
    ids = [c.case_id for c in ALL_MULTISTEP_CASES]
    assert len(set(ids)) == len(ids)


def test_case_ids_match_directive_pattern() -> None:
    expected = {
        f"{prefix}_{n:02d}"
        for prefix in ("R1", "R2", "R3", "R4", "R5")
        for n in range(1, 7)
    }
    actual = {c.case_id for c in ALL_MULTISTEP_CASES}
    assert actual == expected


def test_R1_expects_depth_at_least_one() -> None:
    for c in R1_CASES:
        assert c.expected_min_depth >= 1


def test_R2_expects_depth_at_least_two() -> None:
    for c in R2_CASES:
        assert c.expected_min_depth >= 2


def test_R3_expects_depth_at_least_three() -> None:
    for c in R3_CASES:
        assert c.expected_min_depth >= 3


def test_R4_expects_blocked() -> None:
    for c in R4_CASES:
        assert c.expected_blocked is True
        assert c.expected_final_state is ResolutionState.RESOLUTION_BLOCKED
        assert c.expected_cycle is False


def test_R5_expects_cycle() -> None:
    for c in R5_CASES:
        assert c.expected_cycle is True
        assert c.expected_blocked is True


def test_each_case_has_text() -> None:
    for c in ALL_MULTISTEP_CASES:
        assert c.text.strip()
        assert "Therefore" in c.text or "?" in c.text


def test_ground_truth_fields_present() -> None:
    """Aufgabe 2: each case carries the four required fields."""
    for c in ALL_MULTISTEP_CASES:
        for f in ("expected_final_state", "expected_min_depth",
                  "expected_cycle", "expected_blocked"):
            assert hasattr(c, f)
