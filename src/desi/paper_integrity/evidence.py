"""v13.0 — evidence consistency audit."""
from __future__ import annotations

from .claims import fixture


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def evidence_consistency() -> float:
    """Fraction of claims whose
    evidence_supported flag is true."""
    rows = fixture()
    if not rows:
        return 0.0
    ok = sum(
        1 for c in rows if c.evidence_supported
    )
    return _round(ok / len(rows))


def evidence_gap_count() -> int:
    return sum(
        1 for c in fixture()
        if not c.evidence_supported
    )


__all__ = [
    "evidence_consistency",
    "evidence_gap_count",
]
