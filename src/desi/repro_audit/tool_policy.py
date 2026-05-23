"""Aufgabe 6 — explicit tool-benchmark reproducibility
policy.

The v1.9 tool benchmark contains four ``B_symbolic_math``
cases (TB1-TB4) whose ground truth is
``SHOULD_TOOL_FAIL``: in the v1.9-era environment SymPy
was deliberately absent and these cases were expected to
produce ``TOOL_FAILED`` with ``DEPENDENCY_MISSING``. The
contract is therefore environment-dependent:

* **SymPy absent** — the four cases correctly fail; the
  full benchmark scores 20/20.
* **SymPy present** — the four cases now succeed instead
  of failing, but the ground truth still expects failure;
  the full benchmark scores 16/20.

Two policies are admissible:

* **ENVIRONMENT_CONDITIONAL** — the test asserts the
  expected correct-count *as a function* of
  ``sympy_available``: 20 if absent, 16 if present.
* **SIMULATED_MISSING_DEPENDENCY** — the test runs symbolic
  cases through a mock that always returns
  ``DEPENDENCY_MISSING`` and asserts a constant 20/20.

DESi v4.11 selects the first policy.
"""
from __future__ import annotations

from .enums import ToolReproPolicy


TOOL_REPRO_POLICY: ToolReproPolicy = (
    ToolReproPolicy.ENVIRONMENT_CONDITIONAL
)


def expected_correct_count(*, sympy_available: bool) -> int:
    """Closed expected-correct table under the
    ENVIRONMENT_CONDITIONAL policy.

    The v1.9 ground truth was authored with SymPy absent;
    installing SymPy flips the four symbolic cases from
    correct-failure to incorrect-success.
    """
    return 16 if sympy_available else 20


def expected_symbolic_outcome(*, sympy_available: bool) -> str:
    """The symbolic-cases tool state under the active
    policy. SHOULD_TOOL_FAIL ground truth is matched iff
    SymPy is absent."""
    return "TOOL_SUPPORTED" if sympy_available else "TOOL_FAILED"


__all__ = [
    "TOOL_REPRO_POLICY",
    "expected_correct_count",
    "expected_symbolic_outcome",
]
