"""v17.3 - institutional trust decay.

Trust in sources and institutions decays over the
long horizon. The point is that DESi's GOVERNANCE
does not depend on trust: even as trust falls toward
its floor, stability holds, source quality stays
visible, and dissent is preserved. Falling trust is
surfaced, not amplified.
"""
from __future__ import annotations

from .ecology import run


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def trust_series() -> tuple[float, ...]:
    return tuple(s.trust for s in run())


def trust_range() -> tuple[float, float]:
    vals = trust_series()
    return (_round(min(vals)), _round(max(vals)))


def trust_decayed() -> bool:
    """Trust genuinely falls over the run (start vs
    end), so the stress is real."""
    states = run()
    if len(states) < 2:
        return False
    return states[-1].trust < states[0].trust


def trust_volatility() -> float:
    lo, hi = trust_range()
    return _round(hi - lo)


__all__ = [
    "trust_decayed",
    "trust_range",
    "trust_series",
    "trust_volatility",
]
