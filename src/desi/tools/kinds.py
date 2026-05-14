"""Closed allowlist of tool kinds (v1.9 directive).

The enum is intentionally narrow. Adding a tool requires a code
edit; that edit is itself an audit event. Plugin architecture,
user-defined tools, and dynamic imports are explicitly forbidden.
"""
from __future__ import annotations

from enum import Enum


class ToolKind(str, Enum):
    """The six v1.9-allowed tool kinds.

    * ``PYTHON_DECIMAL``      — fixed-precision arithmetic via the
                                 stdlib ``decimal`` module.
    * ``PYTHON_FRACTIONS``    — exact rational arithmetic via the
                                 stdlib ``fractions`` module.
    * ``PYTHON_DATETIME``     — date / time arithmetic via stdlib.
    * ``PYTHON_COLLECTIONS``  — counting / set / sequence operations
                                 via stdlib.
    * ``SYMPY``                — optional symbolic math. Fails-closed
                                 with ``dependency_missing`` when
                                 sympy is not installed (v1.9 ships
                                 without it; the gate honours that
                                 honestly).
    * ``SET_THEORY``           — pure-Python set operations
                                 (intersection / union / subset) over
                                 explicit element lists.
    """

    PYTHON_DECIMAL = "python_decimal"
    PYTHON_FRACTIONS = "python_fractions"
    PYTHON_DATETIME = "python_datetime"
    PYTHON_COLLECTIONS = "python_collections"
    SYMPY = "sympy"
    SET_THEORY = "set_theory"


# v1.9 directive: the allowlist. Used by ToolGate as the single
# source of truth for whether a proposal may be executed.
ALLOWED_TOOL_KINDS: frozenset[ToolKind] = frozenset(ToolKind)


__all__ = [
    "ALLOWED_TOOL_KINDS",
    "ToolKind",
]
