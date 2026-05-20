"""v16.3 - institutional trust networks and
governance stability.

Institutional trust rises and falls over the
decades (document releases, scandals, media waves).
DESi's governance must stay STABLE through the
oscillation: the verified core holds, evidence is
preserved, inflation stays capped - regardless of
where trust sits.
"""
from __future__ import annotations

from .claim_propagation import (
    independent_evidence_preservation,
)
from .ecology import epistemic_stability, run
from .historical_drift import narrative_inflation_bounded


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def trust_range() -> tuple[float, float]:
    states = run()
    vals = [s.trust for s in states]
    return (_round(min(vals)), _round(max(vals)))


def trust_volatility() -> float:
    """Spread of institutional trust across the run,
    in [0, 1]. High volatility is expected and is
    not itself a failure."""
    lo, hi = trust_range()
    return _round(hi - lo)


def governance_stable() -> bool:
    """Governance holds iff - through all the trust
    swings - the core stays stable, evidence is
    preserved, and inflation stays bounded."""
    return (
        epistemic_stability() >= 0.90
        and independent_evidence_preservation() >= 0.90
        and narrative_inflation_bounded()
    )


__all__ = [
    "governance_stable",
    "trust_range",
    "trust_volatility",
]
