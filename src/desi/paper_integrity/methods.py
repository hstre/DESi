"""v13.0 — method-alignment audit."""
from __future__ import annotations

from .claims import fixture


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def claim_method_alignment() -> float:
    """Fraction of claims whose method_supported
    flag is true. Honest weak papers
    (underpowered but methodologically valid)
    still count - we measure structural method-
    claim alignment, not statistical strength.
    """
    rows = fixture()
    if not rows:
        return 0.0
    aligned = sum(
        1 for c in rows if c.method_supported
    )
    return _round(aligned / len(rows))


def method_gap_count() -> int:
    """Number of claims that do NOT have a
    supporting method record."""
    return sum(
        1 for c in fixture()
        if not c.method_supported
    )


__all__ = [
    "claim_method_alignment",
    "method_gap_count",
]
