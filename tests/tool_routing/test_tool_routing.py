"""Pins the tool-router / arithmetic-tool result to the committed fixtures.

Headline assertion: on the GSM-Symbolic-shaped fixtures, the deterministic tool
makes ZERO arithmetic errors; every residual failure is linguistic (operand
binding / operative-clause semantics) — i.e. the model's job, not the tool's.
This is the routing boundary, pinned.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pytest  # noqa: E402

from desi_router.arithmetic_tool import solve, solve_question  # noqa: E402
from desi_router.tool_router import ToolRoute, ToolRouter  # noqa: E402
from reproduce_tool_routing import run  # noqa: E402


# ---- the tool proper: exact on explicit operands (what a router hands to it) ----

def test_tool_is_exact_on_each_structure():
    assert solve("rate * hours + bonus", [12, 7, 5]) == 89
    assert solve("(items * price) - discount", [9, 4, 6]) == 30
    assert solve("total / groups", [84, 6]) == 14
    # frame-invariant: the ", with added clause" label is not part of the formula
    assert solve("rate * hours + bonus, with added clause", [12, 7, 5]) == 89


def test_tool_raises_when_language_underdelivers():
    # too few operands is an extraction (language) failure, not arithmetic
    with pytest.raises(ValueError):
        solve("rate * hours + bonus", [12, 7])


# ---- end-to-end over the fixtures: 0 arithmetic failures is the point ----

@pytest.fixture(scope="module")
def res():
    return run(words=True)


def test_every_failure_is_linguistic_not_arithmetic(res):
    # arithmetic failures are impossible by construction (exact AST evaluation),
    # so every fixture must be either correct or categorized as a language
    # failure (lexical extraction / operative-clause semantics) — no third bucket
    assert res["correct"] + len(res["lexical"]) + len(res["semantic"]) == res["n"]
    assert "arithmetic" not in res  # no fake "measured zero"; see run()'s comment


def test_all_residual_failures_are_semantic(res):
    # with word numerals, the only misses are operative-clause semantics
    assert len(res["lexical"]) == 0
    assert set(res["semantic"]) == {
        "gsm_p2_t01_i2", "gsm_p2_t01_i3",
        "gsm_p2_t02_i2", "gsm_p2_t02_i3",
        "gsm_p2_t03_i2", "gsm_p2_t03_i3",
    }


def test_accuracy_counts(res):
    assert res["n"] == 33
    assert res["correct"] == 27               # digits + word numerals
    assert run(words=False)["correct"] == 26  # digits only


def test_replay_stable(res):
    assert run(words=True)["digest"] == res["digest"]


# ---- frame-invariance: a decorative clause does not change the answer ----

def test_decorative_clause_is_invariant():
    base = "Mara earns 12 dollars per hour and works 7 hours, then receives a 5 dollar bonus. How much in total?"
    painted = "Mara earns 12 dollars per hour and works 7 hours, then receives a 5 dollar bonus. The office is painted blue. How much in total?"
    s = "rate * hours + bonus"
    assert solve_question(s, base) == solve_question(s, painted) == 89


# ---- the router: tool for computation, model for everything else ----

def test_router_sends_arithmetic_to_the_tool():
    route = ToolRouter().route("math_arithmetic")
    assert isinstance(route, ToolRoute)
    assert route.kind == "tool"
    assert route.tool == "arithmetic_evaluator"
    assert route.deterministic is True
    assert route.expected_cost_usd == 0.0


def test_router_delegates_other_tasks_to_the_model_router():
    route = ToolRouter().route(
        "memory_recall", cost_budget_usd=0.0005, accuracy_target=0.5
    )
    # a model Decision, not a ToolRoute
    assert not isinstance(route, ToolRoute)
    assert hasattr(route, "model") and route.model
