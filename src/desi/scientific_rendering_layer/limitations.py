"""v22.2 - uncertainty visibility and sandbox honesty.

Confirms the document wears its uncertainty openly: explicit
hedges and limitation statements are present, and the
sandbox scope is stated rather than hidden.
"""
from __future__ import annotations

from .structure import full_document, sections

# Hedging / limitation markers that signal visible
# uncertainty.
_HEDGES = (
    "we do not", "we make no", "no claim", "limited to",
    "untested", "future work", "narrow", "not evaluate",
    "leave", "optional", "synthetic", "sandbox",
)
_MIN_HEDGES = 4


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def hedge_count() -> int:
    low = full_document().lower()
    return sum(low.count(h) for h in _HEDGES)


def uncertainty_visibility() -> float:
    """Visible-uncertainty score: min(1, hedges / MIN), in
    [0, 1]."""
    return _round(min(1.0, hedge_count() / _MIN_HEDGES))


def sandbox_honesty() -> bool:
    """The document explicitly limits itself to the sandbox
    and disclaims generalisation."""
    low = full_document().lower()
    return (
        "limited to" in low
        and "beyond the sandbox" in low
        and "Limitations" in sections()
    )


__all__ = [
    "hedge_count",
    "sandbox_honesty",
    "uncertainty_visibility",
]
