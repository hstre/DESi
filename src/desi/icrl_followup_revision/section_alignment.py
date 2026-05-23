"""v23.0 - alignment of DESi claims to base-paper sections.

paper_alignment is the fraction of central DESi claims that
anchor to at least one base-paper problem; section_grounding
is the fraction that cite a concrete sprint source. Together
they answer: is every central claim traceable to a real
problem of the base paper?
"""
from __future__ import annotations

from .paper_mapping import claims


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def paper_alignment() -> float:
    """Fraction of central DESi claims anchored to >= 1 base-
    paper problem, in [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    anchored = sum(1 for c in rows if c.is_anchored())
    return _round(anchored / len(rows))


def section_grounding() -> float:
    """Fraction of central claims that cite a concrete sprint
    source, in [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    grounded = sum(1 for c in rows if c.sprint_source)
    return _round(grounded / len(rows))


def unconnected_claims() -> tuple[str, ...]:
    """Claims with no base-paper anchor (Pflichtfrage 3)."""
    return tuple(
        c.claim_id for c in claims() if not c.is_anchored()
    )


__all__ = [
    "paper_alignment",
    "section_grounding",
    "unconnected_claims",
]
