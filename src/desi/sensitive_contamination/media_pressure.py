"""v17.2 - media pressure and governed narrative
inflation.

Media amplification pushes confidence far above what
the evidence supports. DESi withstands that pressure:
the GOVERNED narrative inflation (the confidence
inflation DESi actually permits) is zero, because
DESi grounds confidence in evidence. The raw attempted
pressure is reported for transparency.
"""
from __future__ import annotations

from .viral_claims import viral_claims


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def attempted_media_pressure() -> float:
    """Mean upward pressure media amplification exerts
    on confidence (asserted minus evidence), in
    [0, 1]. The stress DESi withstands."""
    rows = viral_claims()
    if not rows:
        return 0.0
    total = sum(
        max(0.0, c.asserted_confidence - c.evidence_grade)
        for c in rows
    )
    return _round(total / len(rows))


def narrative_inflation() -> float:
    """Governed narrative inflation: the confidence
    inflation DESi PERMITS to propagate (governed
    minus evidence), in [0, 1]. DESi grounds
    confidence in evidence, so this is 0."""
    rows = viral_claims()
    if not rows:
        return 0.0
    total = sum(
        max(0.0, c.governed_confidence() - c.evidence_grade)
        for c in rows
    )
    return _round(total / len(rows))


def mean_virality() -> float:
    rows = viral_claims()
    if not rows:
        return 0.0
    return _round(
        sum(c.virality for c in rows) / len(rows)
    )


__all__ = [
    "attempted_media_pressure",
    "mean_virality",
    "narrative_inflation",
]
