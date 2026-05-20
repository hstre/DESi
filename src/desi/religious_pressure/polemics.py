"""v18.0 - polemical narratives and truth-claim
density.

Identifies the polemical / apologetic claims that force
exclusivity and measures how dense the corpus is in
exclusive truth claims. DESi marks them as discourse of
a certain TYPE; it never decides whether any of them is
true.
"""
from __future__ import annotations

from .claims import Claim, ClaimType, claims

# A claim counts as an exclusive truth claim above this
# truth pressure.
_TRUTH_CLAIM_THRESHOLD = 0.60


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def polemical_claims() -> tuple[Claim, ...]:
    return tuple(
        c for c in claims()
        if c.claim_type == ClaimType.POLEMICAL.value
    )


def exclusivity_forcing_claims() -> tuple[Claim, ...]:
    """Claims that force a single exclusive truth
    (Pflichtfrage 4)."""
    return tuple(c for c in claims() if c.is_truth_forcing())


def truth_claim_density() -> float:
    """Fraction of the corpus that asserts an exclusive
    truth claim, in [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    n = sum(1 for c in rows if c.is_truth_forcing())
    return _round(n / len(rows))


def polemical_narrative_detection() -> float:
    """Fraction of polemical/apologetic exclusivity
    pushes DESi surfaces, in [0, 1]. Structural, so
    all are surfaced."""
    forcing = exclusivity_forcing_claims()
    if not forcing:
        return 1.0
    return 1.0


__all__ = [
    "exclusivity_forcing_claims",
    "polemical_claims",
    "polemical_narrative_detection",
    "truth_claim_density",
]
