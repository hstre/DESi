"""v17.2 - confidence control and epistemic hygiene.

DESi caps confidence at the evidence grade for every
claim, so false certainty stays at zero however viral
a claim is. Epistemic hygiene composites the
resistance signals: clean virality separation, no
false certainty, and uncertainty kept visible.
"""
from __future__ import annotations

from .myth_growth import myth_visible
from .viral_claims import (
    LOW_CONFIDENCE, viral_claims, virality_separation,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def false_certainty_rate() -> float:
    """Fraction of claims DESi presents above their
    evidence grade, in [0, 1]. Zero - confidence is
    capped at evidence."""
    rows = viral_claims()
    if not rows:
        return 0.0
    leaked = sum(
        1 for c in rows if c.false_certainty_leak()
    )
    return _round(leaked / len(rows))


def uncertainty_preserved_rate() -> float:
    """Fraction of weak-evidence claims that DESi keeps
    at low (uncertain) confidence, in [0, 1]."""
    rows = [
        c for c in viral_claims()
        if c.evidence_grade < LOW_CONFIDENCE
    ]
    if not rows:
        return 1.0
    kept = sum(
        1 for c in rows
        if c.governed_confidence() < LOW_CONFIDENCE
    )
    return _round(kept / len(rows))


def epistemic_hygiene() -> float:
    """Composite resistance to narrative contamination,
    in [0, 1]."""
    return _round((
        virality_separation()
        + (1.0 - false_certainty_rate())
        + uncertainty_preserved_rate()
    ) / 3.0)


__all__ = [
    "epistemic_hygiene",
    "false_certainty_rate",
    "uncertainty_preserved_rate",
]
