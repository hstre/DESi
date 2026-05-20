"""Tests for the six v1.9 tool runners."""
from __future__ import annotations

import pytest

from desi.tools.runners import (
    run_collections,
    run_datetime,
    run_decimal,
    run_fractions,
    run_set_theory,
    run_sympy,
)


# ---------------------------------------------------------------------------
# Decimal
# ---------------------------------------------------------------------------


def test_decimal_simple_addition() -> None:
    assert run_decimal({"expression": "2 + 2"})["value"] == "4"


def test_decimal_multiplication() -> None:
    assert run_decimal({"expression": "17 * 23"})["value"] == "391"


def test_decimal_division_returns_decimal_string() -> None:
    out = run_decimal({"expression": "1 / 4"})["value"]
    assert out.startswith("0.25")


def test_decimal_rejects_non_arithmetic_chars() -> None:
    """Calling with a function-call expression must fail at parse."""
    with pytest.raises(ValueError):
        run_decimal({"expression": "open('etc/passwd')"})


def test_decimal_rejects_attribute_access() -> None:
    with pytest.raises(ValueError):
        run_decimal({"expression": "(1).bit_length()"})


def test_decimal_rejects_string_constants() -> None:
    with pytest.raises(ValueError):
        run_decimal({"expression": "'abc' + 'def'"})


# ---------------------------------------------------------------------------
# Fractions
# ---------------------------------------------------------------------------


def test_fractions_keeps_exactness() -> None:
    out = run_fractions({"expression": "1 / 3 + 1 / 6"})
    assert out["value"] == "1/2"


# ---------------------------------------------------------------------------
# Datetime
# ---------------------------------------------------------------------------


def test_datetime_days_between_2020_full_year() -> None:
    out = run_datetime({
        "operation": "days_between",
        "start": "2020-01-01", "end": "2020-12-31",
    })
    assert out["value"] == "365"   # 2020 is a leap year (366 days; 365 deltas)


def test_datetime_weekday_us_independence_2024() -> None:
    out = run_datetime({"operation": "weekday", "date": "2024-07-04"})
    assert out["value"] == "Thursday"


def test_datetime_add_days_simple() -> None:
    out = run_datetime({
        "operation": "add_days", "date": "2025-01-15", "days": 30,
    })
    assert out["value"] == "2025-02-14"


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


def test_collections_count_vowels_mississippi() -> None:
    out = run_collections({
        "operation": "count_vowels", "text": "mississippi",
    })
    assert out["value"] == "4"


def test_collections_count_letter_s_mississippi() -> None:
    out = run_collections({
        "operation": "count_letter", "text": "mississippi", "letter": "s",
    })
    assert out["value"] == "4"


def test_collections_count_distinct_banana() -> None:
    out = run_collections({
        "operation": "count_distinct", "items": list("banana"),
    })
    assert out["value"] == "3"


# ---------------------------------------------------------------------------
# Sympy (fail-closed when not installed)
# ---------------------------------------------------------------------------


def test_sympy_fail_closes_when_unavailable() -> None:
    """v1.9 ships without sympy. The runner must surface a typed
    ModuleNotFoundError; the gate converts that to TOOL_FAILED."""
    try:
        import sympy as _   # noqa: F401
        pytest.skip("sympy is installed in this environment")
    except ModuleNotFoundError:
        pass
    with pytest.raises(ModuleNotFoundError):
        run_sympy({"operation": "solve", "lhs": "x", "rhs": "1"})


# ---------------------------------------------------------------------------
# Set theory
# ---------------------------------------------------------------------------


def test_set_intersection() -> None:
    out = run_set_theory({
        "operation": "intersection",
        "a": ["1", "2", "3"], "b": ["2", "3", "4"],
    })
    assert out["value"] == ["2", "3"]


def test_set_is_subset_true() -> None:
    out = run_set_theory({
        "operation": "is_subset",
        "a": ["1", "2"], "b": ["1", "2", "3"],
    })
    assert out["value"] == "true"


def test_set_is_subset_false() -> None:
    out = run_set_theory({
        "operation": "is_subset",
        "a": ["1", "5"], "b": ["1", "2", "3"],
    })
    assert out["value"] == "false"


# ---------------------------------------------------------------------------
# Runner determinism (call twice → same output)
# ---------------------------------------------------------------------------


def test_decimal_runner_is_deterministic() -> None:
    a = run_decimal({"expression": "(1+2)*3"})
    b = run_decimal({"expression": "(1+2)*3"})
    assert a == b
