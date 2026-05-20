"""Tool runners — pure stdlib implementations of the v1.9 allowlist.

Every runner is a pure function: it takes a typed input payload
and returns a typed output dict. No filesystem writes, no network
access, no subprocess, no eval / exec, no dynamic imports beyond
the closed allowlist (and even those imports happen at module
load time, not at call time).

The arithmetic runner uses a hand-walked AST evaluator instead of
``eval()`` to satisfy the directive's hard ban on eval / exec.
"""
from __future__ import annotations

import ast
import sys
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal, getcontext
from fractions import Fraction
from typing import Any


# v1.9: arithmetic precision floor. 50 digits is generous for
# benchmark tasks while staying audit-deterministic.
getcontext().prec = 50


_ALLOWED_AST_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub, ast.FloorDiv,
)


def _eval_arith_node(node: ast.AST, kind: str) -> Any:
    """Walk an AST and evaluate it with Decimal or Fraction arithmetic.

    Refuses any node not in :data:`_ALLOWED_AST_NODES` so the
    evaluator cannot run arbitrary code.
    """
    if not isinstance(node, _ALLOWED_AST_NODES):
        raise ValueError(f"unsupported AST node: {type(node).__name__}")
    if isinstance(node, ast.Expression):
        return _eval_arith_node(node.body, kind)
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(
                f"unsupported constant: {type(node.value).__name__}"
            )
        if kind == "decimal":
            return Decimal(str(node.value))
        return Fraction(node.value).limit_denominator(10**12)
    if isinstance(node, ast.UnaryOp):
        v = _eval_arith_node(node.operand, kind)
        return -v if isinstance(node.op, ast.USub) else v
    # BinOp
    l = _eval_arith_node(node.left, kind)
    r = _eval_arith_node(node.right, kind)
    op = node.op
    if isinstance(op, ast.Add):       return l + r
    if isinstance(op, ast.Sub):       return l - r
    if isinstance(op, ast.Mult):      return l * r
    if isinstance(op, ast.Div):       return l / r
    if isinstance(op, ast.Mod):       return l % r
    if isinstance(op, ast.Pow):       return l ** r
    if isinstance(op, ast.FloorDiv):  return l // r
    raise ValueError(f"unsupported operator: {type(op).__name__}")


# ---------------------------------------------------------------------------
# PYTHON_DECIMAL
# ---------------------------------------------------------------------------


def run_decimal(payload: dict[str, Any]) -> dict[str, Any]:
    """Decimal arithmetic over a string expression.

    Payload: ``{"expression": "2 + 2"}``.
    Output:  ``{"value": "4", "kind": "decimal"}``.
    """
    if "expression" not in payload:
        raise ValueError("missing 'expression' in payload")
    expr = str(payload["expression"]).strip()
    if not expr:
        raise ValueError("empty expression")
    tree = ast.parse(expr, mode="eval")
    result = _eval_arith_node(tree, kind="decimal")
    return {"value": str(result), "kind": "decimal"}


def run_fractions(payload: dict[str, Any]) -> dict[str, Any]:
    """Exact rational arithmetic over a string expression."""
    if "expression" not in payload:
        raise ValueError("missing 'expression' in payload")
    expr = str(payload["expression"]).strip()
    if not expr:
        raise ValueError("empty expression")
    tree = ast.parse(expr, mode="eval")
    result = _eval_arith_node(tree, kind="fraction")
    if isinstance(result, Fraction):
        return {
            "value": str(result),
            "numerator": str(result.numerator),
            "denominator": str(result.denominator),
            "kind": "fraction",
        }
    return {"value": str(result), "kind": "fraction"}


# ---------------------------------------------------------------------------
# PYTHON_DATETIME
# ---------------------------------------------------------------------------


def run_datetime(payload: dict[str, Any]) -> dict[str, Any]:
    """Date / time operations with explicit ISO inputs.

    Operations:
    * ``days_between`` — start, end → integer day delta.
    * ``weekday``      — date → English weekday name.
    * ``add_days``     — date, days → resulting date (ISO).
    """
    op = payload.get("operation")
    if op == "days_between":
        d1 = date.fromisoformat(payload["start"])
        d2 = date.fromisoformat(payload["end"])
        return {"value": str((d2 - d1).days), "operation": op}
    if op == "weekday":
        d = date.fromisoformat(payload["date"])
        return {"value": d.strftime("%A"), "operation": op}
    if op == "add_days":
        d = date.fromisoformat(payload["date"])
        delta = int(payload["days"])
        return {
            "value": (d + timedelta(days=delta)).isoformat(),
            "operation": op,
        }
    raise ValueError(f"unknown datetime operation: {op!r}")


# ---------------------------------------------------------------------------
# PYTHON_COLLECTIONS
# ---------------------------------------------------------------------------


_VOWELS = frozenset("aeiouAEIOU")


def run_collections(payload: dict[str, Any]) -> dict[str, Any]:
    """Counting / sequence operations.

    Operations:
    * ``count_vowels``    — count vowels in text.
    * ``count_chars``     — count characters in text (or matching specific chars).
    * ``count_distinct``  — distinct elements in a list.
    * ``count_letter``    — occurrences of a single character.
    """
    op = payload.get("operation")
    if op == "count_vowels":
        text = str(payload["text"])
        return {"value": str(sum(1 for c in text if c in _VOWELS)),
                "operation": op}
    if op == "count_chars":
        text = str(payload["text"])
        chars = payload.get("chars")
        if chars:
            target = set(str(chars).lower())
            return {"value": str(sum(1 for c in text.lower() if c in target)),
                    "operation": op}
        return {"value": str(len(text)), "operation": op}
    if op == "count_distinct":
        items = list(payload["items"])
        return {"value": str(len(set(items))), "operation": op}
    if op == "count_letter":
        text = str(payload["text"])
        letter = str(payload["letter"]).lower()
        if len(letter) != 1:
            raise ValueError("'letter' must be a single character")
        return {"value": str(sum(1 for c in text.lower() if c == letter)),
                "operation": op}
    raise ValueError(f"unknown collections operation: {op!r}")


# ---------------------------------------------------------------------------
# SYMPY (optional; fail-closed if unavailable)
# ---------------------------------------------------------------------------


def run_sympy(payload: dict[str, Any]) -> dict[str, Any]:
    """Symbolic math via sympy.

    sympy is **not** part of the v1.9 dependency set. If it is not
    installed, this runner raises ``ModuleNotFoundError``; the
    ToolGate converts that into a TOOL_FAILED result with reason
    ``dependency_missing``.
    """
    try:
        import sympy  # type: ignore
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "sympy is not installed; run_sympy fail-closes per directive"
        ) from exc
    op = payload.get("operation")
    if op == "solve":
        from sympy import Eq, solve, symbols, sympify   # noqa: F401
        var_name = str(payload.get("variable", "x"))
        var = symbols(var_name)
        lhs = sympify(payload["lhs"])
        rhs = sympify(payload["rhs"])
        sols = solve(Eq(lhs, rhs), var)
        return {"value": [str(s) for s in sols], "operation": op}
    if op == "simplify":
        from sympy import simplify, sympify   # noqa: F401
        return {"value": str(simplify(sympify(payload["expression"]))),
                "operation": op}
    raise ValueError(f"unknown sympy operation: {op!r}")


# ---------------------------------------------------------------------------
# SET_THEORY
# ---------------------------------------------------------------------------


def run_set_theory(payload: dict[str, Any]) -> dict[str, Any]:
    """Set operations over explicit element lists.

    Operations: ``intersection``, ``union``, ``difference``,
    ``symmetric_difference``, ``is_subset``, ``is_superset``,
    ``is_disjoint``.
    """
    op = payload.get("operation")
    a = set(payload.get("a", []))
    b = set(payload.get("b", []))
    if op == "intersection":
        return {"value": sorted(a & b, key=str), "operation": op}
    if op == "union":
        return {"value": sorted(a | b, key=str), "operation": op}
    if op == "difference":
        return {"value": sorted(a - b, key=str), "operation": op}
    if op == "symmetric_difference":
        return {"value": sorted(a ^ b, key=str), "operation": op}
    if op == "is_subset":
        return {"value": str(a <= b).lower(), "operation": op}
    if op == "is_superset":
        return {"value": str(a >= b).lower(), "operation": op}
    if op == "is_disjoint":
        return {"value": str(a.isdisjoint(b)).lower(), "operation": op}
    raise ValueError(f"unknown set operation: {op!r}")


# ---------------------------------------------------------------------------
# Runner registry (consumed by ToolGate)
# ---------------------------------------------------------------------------


from .kinds import ToolKind


RUNNERS: dict[ToolKind, dict[str, Any]] = {
    ToolKind.PYTHON_DECIMAL: {
        "module_name": "desi.tools.runners",
        "function_name": "run_decimal",
        "function": run_decimal,
        "tool_name": "python_decimal",
        "tool_version": sys.version.split()[0],
    },
    ToolKind.PYTHON_FRACTIONS: {
        "module_name": "desi.tools.runners",
        "function_name": "run_fractions",
        "function": run_fractions,
        "tool_name": "python_fractions",
        "tool_version": sys.version.split()[0],
    },
    ToolKind.PYTHON_DATETIME: {
        "module_name": "desi.tools.runners",
        "function_name": "run_datetime",
        "function": run_datetime,
        "tool_name": "python_datetime",
        "tool_version": sys.version.split()[0],
    },
    ToolKind.PYTHON_COLLECTIONS: {
        "module_name": "desi.tools.runners",
        "function_name": "run_collections",
        "function": run_collections,
        "tool_name": "python_collections",
        "tool_version": sys.version.split()[0],
    },
    ToolKind.SYMPY: {
        "module_name": "desi.tools.runners",
        "function_name": "run_sympy",
        "function": run_sympy,
        "tool_name": "sympy",
        "tool_version": "optional-not-pinned",
    },
    ToolKind.SET_THEORY: {
        "module_name": "desi.tools.runners",
        "function_name": "run_set_theory",
        "function": run_set_theory,
        "tool_name": "set_theory",
        "tool_version": sys.version.split()[0],
    },
}


__all__ = [
    "RUNNERS",
    "run_collections",
    "run_datetime",
    "run_decimal",
    "run_fractions",
    "run_set_theory",
    "run_sympy",
]
