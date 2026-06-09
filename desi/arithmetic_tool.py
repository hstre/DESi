"""Deterministic arithmetic tool — the "logic" arm of a tool-router.

DESi's thesis is "LLM for language, rules for logic." At the routing level this
means: when a task reduces to a known arithmetic structure, do not spend a
stochastic model on the computation — hand it to a deterministic evaluator that
is exact, free, microsecond-fast, and byte-identical across runs.

This module is that evaluator. Given a structure expression (e.g.
``"rate * hours + bonus"``) and operands, it computes the answer with a tiny
safe AST evaluator — no ``eval`` of arbitrary code, only +, -, *, / and unary
minus over named operands.

What it deliberately does NOT do: understand language. Extracting the operands
and judging whether an added clause changes the computation is the model's job.
``extract_operands`` is only a naive convenience for the reproduction harness;
its failures (word numerals, operative clauses) localize exactly where language
is irreplaceable — see scripts/reproduce_tool_routing.py.
"""
from __future__ import annotations

import ast
import operator
import re

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

# Small word-numeral table — enough to show that a lexical miss ("Nine") is a
# language problem, not an arithmetic one. Not a general NL number parser.
_WORD_NUMERALS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}


def structure_expr_and_vars(structure: str) -> tuple[str, list[str]]:
    """Split a structure string into (arithmetic expression, ordered variables).

    Trailing prose such as ", with added clause" is dropped — it is a label, not
    part of the formula.
    """
    expr = structure.split(",")[0].strip()
    seen: list[str] = []
    for name in re.findall(r"[A-Za-z_]\w*", expr):
        if name not in seen:
            seen.append(name)
    return expr, seen


def _eval(node: ast.AST, env: dict[str, float]) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left, env), _eval(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand, env))
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    raise ValueError(f"unsupported expression node: {ast.dump(node)}")


def solve(structure: str, operands: list[int]) -> int | float:
    """Compute the answer from a structure and explicitly supplied operands.

    This is the tool proper: pure, total over its inputs, and exact. Raises if
    fewer operands than the structure needs (an upstream/language failure, not
    an arithmetic one).
    """
    expr, variables = structure_expr_and_vars(structure)
    if len(operands) < len(variables):
        raise ValueError(
            f"need {len(variables)} operands {variables}, got {len(operands)}"
        )
    env = dict(zip(variables, operands))
    value = _eval(ast.parse(expr, mode="eval"), env)
    return int(value) if float(value).is_integer() else value


def extract_operands(question: str, *, words: bool = True) -> list[int]:
    """Naive left-to-right operand extraction (digits, optionally word numerals).

    Intentionally simple — this is the brittle, language-bound step. It exists
    only so the harness can run end-to-end and *show* where extraction fails.
    """
    ops: list[int] = []
    for tok in re.findall(r"-?\d+|[A-Za-z]+", question):
        if re.fullmatch(r"-?\d+", tok):
            ops.append(int(tok))
        elif words and tok.lower() in _WORD_NUMERALS:
            ops.append(_WORD_NUMERALS[tok.lower()])
    return ops


def solve_question(structure: str, question: str, *, words: bool = True) -> int | float:
    """End-to-end naive path: extract operands from text, then compute.

    Convenience for the harness only. The computation is exact; any wrong answer
    here is an extraction/semantic (language) failure, never arithmetic.
    """
    return solve(structure, extract_operands(question, words=words))
