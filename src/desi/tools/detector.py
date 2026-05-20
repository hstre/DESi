"""ToolDetector — pattern-based proposer for computable structures.

The detector scans free-form text for tightly-shaped computational
patterns (a numeric arithmetic expression, an ISO date pair, a
"how many vowels in 'X'" form, etc.) and returns a
:class:`desi.tools.proposal.ToolUseProposal` when a pattern fires.

Patterns are intentionally narrow. The detector returns ``None``
on anything ambiguous so the directive's "false tool temptation"
category (Cat E in the v1.9 mini-benchmark) blocks rather than
dispatching to a tool that cannot possibly answer.

There is no LLM call, no learned classifier, and no dynamic
import. Adding a new pattern requires a code edit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .kinds import ToolKind
from .proposal import ToolUseProposal, make_run_id
from .runners import RUNNERS


# ---------------------------------------------------------------------------
# Closed pattern library
# ---------------------------------------------------------------------------


# Arithmetic forms.
_RE_ARITH_QUESTION = re.compile(
    r"^\s*(?:what\s+is|compute|calculate|evaluate)\s+"
    r"(?P<expr>[\d\.\s\+\-\*\/\(\)]+)\??\s*$",
    re.IGNORECASE,
)

# "Is 144 = 12 * 12?" → arithmetic refutation/support.
_RE_ARITH_EQUALITY = re.compile(
    r"^\s*is\s+(?P<lhs>[\d\.\s\+\-\*\/\(\)]+)\s*=\s*"
    r"(?P<rhs>[\d\.\s\+\-\*\/\(\)]+)\??\s*$",
    re.IGNORECASE,
)


_RE_DATE_DIFF = re.compile(
    r"^\s*how\s+many\s+days\s+between\s+"
    r"(?P<a>\d{4}-\d{2}-\d{2})\s+and\s+"
    r"(?P<b>\d{4}-\d{2}-\d{2})\??\s*$",
    re.IGNORECASE,
)

_RE_DATE_WEEKDAY = re.compile(
    r"^\s*(?:what\s+weekday\s+(?:was|is)|on\s+what\s+day\s+of\s+the\s+week\s+(?:was|is))\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\??\s*$",
    re.IGNORECASE,
)

_RE_DATE_ADD = re.compile(
    r"^\s*add\s+(?P<days>\d+)\s+days?\s+to\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\??\s*$",
    re.IGNORECASE,
)


_RE_VOWEL_COUNT = re.compile(
    r"^\s*how\s+many\s+vowels\s+(?:are\s+)?in\s+"
    r"['\"](?P<text>[^'\"]+)['\"]\??\s*$",
    re.IGNORECASE,
)

_RE_LETTER_COUNT = re.compile(
    r"^\s*how\s+many\s+(?P<letter>[a-z])'?s?\s+(?:are\s+)?in\s+"
    r"['\"](?P<text>[^'\"]+)['\"]\??\s*$",
    re.IGNORECASE,
)

_RE_DISTINCT_COUNT = re.compile(
    r"^\s*how\s+many\s+(?:distinct|unique)\s+(?:letters|characters)\s+"
    r"(?:are\s+)?in\s+['\"](?P<text>[^'\"]+)['\"]\??\s*$",
    re.IGNORECASE,
)


# Set theory: "Is {1,2} subset of {1,2,3}?", "Intersection of {1,2} and {2,3}".
_RE_SET_LITERAL = re.compile(r"\{([^{}]*)\}")


def _parse_set(text: str) -> set | None:
    """Parse a literal ``{1,2,3}`` into a set of strings.

    Conservative: any element that doesn't lex cleanly raises.
    Returns None when the text doesn't look like a set literal.
    """
    m = _RE_SET_LITERAL.search(text)
    if m is None:
        return None
    inside = m.group(1).strip()
    if not inside:
        return set()
    # Split on commas, strip quotes / whitespace.
    items = [x.strip().strip("\"'") for x in inside.split(",") if x.strip()]
    return set(items)


_RE_SET_SUBSET = re.compile(
    r"^\s*is\s+\{(?P<a>[^}]*)\}\s+(?:a\s+)?subset\s+of\s+\{(?P<b>[^}]*)\}\??\s*$",
    re.IGNORECASE,
)
_RE_SET_INTER = re.compile(
    r"^\s*intersection\s+of\s+\{(?P<a>[^}]*)\}\s+and\s+\{(?P<b>[^}]*)\}\.?\s*$",
    re.IGNORECASE,
)


# Symbolic math (sympy).
_RE_SYMPY_SOLVE = re.compile(
    r"^\s*solve\s+(?P<lhs>[\w\d\s\+\-\*\/\^\(\)]+?)\s*=\s*"
    r"(?P<rhs>[\w\d\s\+\-\*\/\^\(\)]+?)\s+for\s+(?P<var>[a-z])\.?\s*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DetectionRationale:
    pattern_name: str
    matched_text: str


class ToolDetector:
    """Pattern-driven tool proposer.

    The detector is stateless; every call re-runs the closed
    pattern set. Returns ``None`` for any text that doesn't match
    a pattern — falling through to the v1.7 audit pipeline.
    """

    def detect(
        self,
        text: str,
        *,
        run_id: str | None = None,
    ) -> ToolUseProposal | None:
        if not isinstance(text, str) or not text.strip():
            return None
        text = text.strip()
        run_id = run_id or make_run_id()

        # ---------- Arithmetic ----------
        m = _RE_ARITH_QUESTION.match(text)
        if m:
            expr = m.group("expr").strip()
            if expr and any(c in expr for c in "+-*/"):
                return _build(
                    ToolKind.PYTHON_DECIMAL,
                    {"expression": expr},
                    run_id, "arith_question",
                )
        m = _RE_ARITH_EQUALITY.match(text)
        if m:
            return _build(
                ToolKind.PYTHON_DECIMAL,
                {"expression": f"({m.group('lhs').strip()}) - ({m.group('rhs').strip()})"},
                run_id, "arith_equality",
            )

        # ---------- Datetime ----------
        m = _RE_DATE_DIFF.match(text)
        if m:
            return _build(
                ToolKind.PYTHON_DATETIME,
                {"operation": "days_between",
                 "start": m.group("a"), "end": m.group("b")},
                run_id, "date_diff",
            )
        m = _RE_DATE_WEEKDAY.match(text)
        if m:
            return _build(
                ToolKind.PYTHON_DATETIME,
                {"operation": "weekday", "date": m.group("date")},
                run_id, "date_weekday",
            )
        m = _RE_DATE_ADD.match(text)
        if m:
            return _build(
                ToolKind.PYTHON_DATETIME,
                {"operation": "add_days",
                 "date": m.group("date"), "days": int(m.group("days"))},
                run_id, "date_add",
            )

        # ---------- Counting ----------
        m = _RE_VOWEL_COUNT.match(text)
        if m:
            return _build(
                ToolKind.PYTHON_COLLECTIONS,
                {"operation": "count_vowels", "text": m.group("text")},
                run_id, "vowel_count",
            )
        m = _RE_LETTER_COUNT.match(text)
        if m:
            return _build(
                ToolKind.PYTHON_COLLECTIONS,
                {"operation": "count_letter",
                 "text": m.group("text"),
                 "letter": m.group("letter")},
                run_id, "letter_count",
            )
        m = _RE_DISTINCT_COUNT.match(text)
        if m:
            return _build(
                ToolKind.PYTHON_COLLECTIONS,
                {"operation": "count_distinct",
                 "items": list(m.group("text"))},
                run_id, "distinct_count",
            )

        # ---------- Set theory ----------
        m = _RE_SET_SUBSET.match(text)
        if m:
            return _build(
                ToolKind.SET_THEORY,
                {"operation": "is_subset",
                 "a": [x.strip() for x in m.group("a").split(",") if x.strip()],
                 "b": [x.strip() for x in m.group("b").split(",") if x.strip()]},
                run_id, "set_subset",
            )
        m = _RE_SET_INTER.match(text)
        if m:
            return _build(
                ToolKind.SET_THEORY,
                {"operation": "intersection",
                 "a": [x.strip() for x in m.group("a").split(",") if x.strip()],
                 "b": [x.strip() for x in m.group("b").split(",") if x.strip()]},
                run_id, "set_intersection",
            )

        # ---------- Sympy (symbolic) ----------
        m = _RE_SYMPY_SOLVE.match(text)
        if m:
            return _build(
                ToolKind.SYMPY,
                {"operation": "solve",
                 "lhs": m.group("lhs").strip(),
                 "rhs": m.group("rhs").strip(),
                 "variable": m.group("var")},
                run_id, "sympy_solve",
            )

        return None


def _build(
    kind: ToolKind,
    payload: dict,
    run_id: str,
    pattern: str,
) -> ToolUseProposal:
    entry = RUNNERS[kind]
    return ToolUseProposal.build(
        tool_kind=kind,
        module_name=entry["module_name"],
        function_name=entry["function_name"],
        input_payload=payload,
        run_id=run_id,
        rationale=f"matched pattern: {pattern}",
    )


__all__ = [
    "ToolDetector",
]
