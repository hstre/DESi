"""v20.3 - authority drift.

Authority drift is the slow accumulation of optimisation
authority by DESi (or the wild). DESi bounds it: the
governed authority drift grows in a bounded, saturating way
and stays well below takeover, so neither agent becomes the
hidden optimiser.
"""
from __future__ import annotations

from .ecology import mean_attempted_pressure, run

_DRIFT_CEILING = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def authority_drift() -> float:
    """Governed authority drift at the end of the run, in
    [0, 1]. Bounded by DESi's self-limitation."""
    states = run()
    if not states:
        return 0.0
    return states[-1].authority_drift


def authority_drift_bounded() -> bool:
    states = run()
    vals = [s.authority_drift for s in states]
    monotone = all(
        vals[i] <= vals[i + 1] + 1e-9
        for i in range(len(vals) - 1)
    )
    return monotone and vals[-1] <= _DRIFT_CEILING


def authority_resistance() -> float:
    """1 - governed authority drift, in [0, 1]."""
    return _round(1.0 - authority_drift())


def attempted_pressure() -> float:
    return mean_attempted_pressure()


__all__ = [
    "attempted_pressure",
    "authority_drift",
    "authority_drift_bounded",
    "authority_resistance",
]
