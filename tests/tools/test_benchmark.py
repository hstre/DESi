"""Tests for the v1.9 mini-benchmark — 20 cases, precision = 1.0."""
from __future__ import annotations

import pytest

from desi.memory.claim import ClaimState
from desi.tools import (
    ALL_TOOL_CASES,
    ToolBenchmarkRunner,
    ToolCategory,
    ToolGroundTruth,
    cases_by_category,
)


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------


def test_total_case_count_is_twenty() -> None:
    assert len(ALL_TOOL_CASES) == 20


def test_each_category_has_four_cases() -> None:
    for cat in ToolCategory:
        assert len(cases_by_category(cat)) == 4


def test_categories_form_a_closed_set_of_five() -> None:
    assert len(list(ToolCategory)) == 5


def test_all_case_ids_unique() -> None:
    ids = [c.case_id for c in ALL_TOOL_CASES]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


def test_runner_returns_one_result_per_case() -> None:
    run = ToolBenchmarkRunner().run()
    assert len(run.results) == 20


def test_result_carries_required_fields() -> None:
    run = ToolBenchmarkRunner().run()
    for r in run.results:
        assert hasattr(r, "case")
        assert hasattr(r, "proposal")
        assert hasattr(r, "tool_result")
        assert hasattr(r, "correct")
        assert hasattr(r, "rationale")


# ---------------------------------------------------------------------------
# Hard constraints (Aufgabe 8)
# ---------------------------------------------------------------------------


def test_precision_is_one_dot_zero() -> None:
    """Of all TOOL_SUPPORTED outputs, every value matches expected."""
    run = ToolBenchmarkRunner().run()
    supported = [r for r in run.results
                 if r.tool_result is not None and r.tool_result.succeeded]
    correct = sum(1 for r in supported if r.correct)
    assert len(supported) > 0
    assert correct == len(supported), (
        f"{len(supported) - correct} of {len(supported)} TOOL_SUPPORTED "
        "outputs were wrong — precision violated"
    )


def test_no_false_positives_in_mini_benchmark() -> None:
    """SHOULD_NOT_DISPATCH cases must not produce a tool result."""
    run = ToolBenchmarkRunner().run()
    for r in run.results:
        if r.case.ground_truth is ToolGroundTruth.SHOULD_NOT_DISPATCH:
            assert r.proposal is None, (
                f"{r.case.case_id} dispatched a tool on a "
                "non-computable input"
            )


def test_all_cases_grade_correct_under_v19() -> None:
    """v1.9 mini-benchmark target: 20/20 correct."""
    run = ToolBenchmarkRunner().run()
    correct = sum(1 for r in run.results if r.correct)
    assert correct == 20


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


def test_two_runs_produce_identical_per_case_hashes() -> None:
    a = ToolBenchmarkRunner().run()
    b = ToolBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        if ra.tool_result is None:
            assert rb.tool_result is None
            continue
        if ra.tool_result.provenance is None:
            assert rb.tool_result.provenance is None
            continue
        # Input + output hashes are deterministic.
        assert (ra.tool_result.provenance.input_hash
                == rb.tool_result.provenance.input_hash), ra.case.case_id
        assert (ra.tool_result.provenance.output_hash
                == rb.tool_result.provenance.output_hash), ra.case.case_id


# ---------------------------------------------------------------------------
# Tool never directly = LOGICALLY_SUPPORTED
# ---------------------------------------------------------------------------


def test_no_tool_result_state_is_logically_supported() -> None:
    run = ToolBenchmarkRunner().run()
    for r in run.results:
        if r.tool_result is None:
            continue
        assert r.tool_result.state is not ClaimState.LOGICALLY_SUPPORTED, (
            f"{r.case.case_id}: tool result is LOGICALLY_SUPPORTED — "
            "directive violation"
        )


# ---------------------------------------------------------------------------
# Cat-B fail-closes (sympy unavailable in v1.9)
# ---------------------------------------------------------------------------


def test_category_b_all_tool_failed_under_v19() -> None:
    """sympy is not installed; Cat B must produce TOOL_FAILED with
    DEPENDENCY_MISSING for every case."""
    try:
        import sympy as _   # noqa: F401
        pytest.skip("sympy is installed in this environment")
    except ModuleNotFoundError:
        pass
    run = ToolBenchmarkRunner().run()
    cat_b = [r for r in run.results
             if r.case.category is ToolCategory.B_SYMBOLIC_MATH]
    assert len(cat_b) == 4
    for r in cat_b:
        assert r.tool_result is not None
        assert r.tool_result.state is ClaimState.TOOL_FAILED
        assert r.tool_result.failure_reason == "dependency_missing"
