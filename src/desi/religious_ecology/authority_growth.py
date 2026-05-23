"""v18.3 - authority drift.

Authority claims and political instrumentalization push
toward a centralised, single epistemic authority. DESi
caps that drift: the GOVERNED authority drift grows in a
bounded, saturating way and stays well below takeover.
The raw pressure is reported separately.
"""
from __future__ import annotations

from .ecology import mean_attempted_pressure, run

_DRIFT_CEILING = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def authority_drift() -> float:
    """Governed authority drift at the end of the run, in
    [0, 1]. Bounded by DESi's resistance."""
    states = run()
    if not states:
        return 0.0
    return states[-1].authority_drift


def authority_drift_bounded() -> bool:
    """Drift is monotone and stays below the ceiling -
    visible but never a takeover."""
    states = run()
    vals = [s.authority_drift for s in states]
    monotone = all(
        vals[i] <= vals[i + 1] + 1e-9
        for i in range(len(vals) - 1)
    )
    return monotone and vals[-1] <= _DRIFT_CEILING


def attempted_authority_pressure() -> float:
    return mean_attempted_pressure()


__all__ = [
    "attempted_authority_pressure",
    "authority_drift",
    "authority_drift_bounded",
]
