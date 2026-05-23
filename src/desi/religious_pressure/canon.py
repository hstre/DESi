"""v18.0 - canonical structure and dogmatic pressure.

Maps the canonical claims and quantifies the ambient
DOGMATIC PRESSURE - the push toward a single, exclusive,
unified truth. DESi MEASURES this pressure and makes it
visible; it never yields to it. High metaphysical load
is recorded, never adjudicated (theological meaning is
outside empirical verification).
"""
from __future__ import annotations

from .claims import Claim, ClaimType, claims


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def canonical_claims() -> tuple[Claim, ...]:
    return tuple(
        c for c in claims()
        if c.claim_type == ClaimType.CANONICAL.value
    )


def metaphysical_load() -> float:
    """Mean metaphysical load across the corpus, in
    [0, 1]. A measurement, not a judgement."""
    rows = claims()
    if not rows:
        return 0.0
    return _round(
        sum(c.metaphysical_load for c in rows) / len(rows)
    )


def dogmatic_pressure() -> float:
    """Ambient pressure toward dogmatic unification: the
    mean truth-pressure across all claims, in [0, 1].
    DESi detects and surfaces it without adopting it."""
    rows = claims()
    if not rows:
        return 0.0
    return _round(
        sum(c.truth_pressure for c in rows) / len(rows)
    )


def high_metaphysical_load_claims() -> tuple[Claim, ...]:
    """Pflichtfrage 2: which claims carry high
    metaphysical load (>= 0.70)."""
    return tuple(
        c for c in claims() if c.metaphysical_load >= 0.70
    )


__all__ = [
    "canonical_claims",
    "dogmatic_pressure",
    "high_metaphysical_load_claims",
    "metaphysical_load",
]
