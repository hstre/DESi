"""v4.11 — explicit tool benchmark environment policy.

These tests replace any implicit assumption that the v1.9
tool benchmark always scores 20/20: the expected count is
declared *as a function* of ``sympy_available``.
"""
from __future__ import annotations

from desi.repro_audit import (
    TOOL_REPRO_POLICY, ToolReproPolicy,
    expected_correct_count, expected_symbolic_outcome,
    fingerprint,
)
from desi.tools.benchmark import ToolBenchmarkRunner


def test_policy_is_environment_conditional() -> None:
    assert TOOL_REPRO_POLICY == (
        ToolReproPolicy.ENVIRONMENT_CONDITIONAL
    )


def test_expected_count_table_is_explicit() -> None:
    """Closed table — both halves of the if-sympy fork are
    pinned by the policy."""
    assert expected_correct_count(sympy_available=False) == 20
    assert expected_correct_count(sympy_available=True) == 16


def test_expected_symbolic_outcome_table_is_explicit() -> None:
    assert expected_symbolic_outcome(
        sympy_available=False,
    ) == "TOOL_FAILED"
    assert expected_symbolic_outcome(
        sympy_available=True,
    ) == "TOOL_SUPPORTED"


def test_live_tool_benchmark_matches_policy() -> None:
    """Live tool-benchmark correct-count must match the
    policy's prediction for the current environment."""
    env = fingerprint()
    run = ToolBenchmarkRunner().run()
    correct = sum(1 for r in run.results if r.correct)
    assert correct == expected_correct_count(
        sympy_available=env.sympy_available,
    ), (correct, env.sympy_available)
