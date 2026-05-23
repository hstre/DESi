"""v17.3 - uncertainty governance over the long
horizon.

DESi preserves dissent at every step and bounds
mythologization growth. Together with high stability
and visible source quality, this is what "governance
integrity" means here: the contaminated space is held
stable without the system itself becoming an
authority.
"""
from __future__ import annotations

from .claim_propagation import source_quality_visibility
from .ecology import epistemic_stability, run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def dissent_preservation() -> float:
    """Fraction of steps at which dissent is preserved,
    in [0, 1]."""
    states = run()
    if not states:
        return 1.0
    kept = sum(1 for s in states if s.dissent_preserved)
    return _round(kept / len(states))


def mythologization_growth() -> float:
    states = run()
    if not states:
        return 0.0
    return _round(
        states[-1].mythologization
        - states[0].mythologization
    )


def mythologization_bounded() -> bool:
    """Myth grows monotonically but stays below the
    hygiene cap - visible, never runaway."""
    states = run()
    vals = [s.mythologization for s in states]
    monotone = all(
        vals[i] <= vals[i + 1] + 1e-9
        for i in range(len(vals) - 1)
    )
    return monotone and vals[-1] <= 0.28


def governance_integrity() -> float:
    """Composite: the space is held stable, source
    quality stays visible, and dissent is preserved -
    in [0, 1]."""
    return _round((
        epistemic_stability()
        + source_quality_visibility()
        + dissent_preservation()
    ) / 3.0)


__all__ = [
    "dissent_preservation",
    "governance_integrity",
    "mythologization_bounded",
    "mythologization_growth",
]
