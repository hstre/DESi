"""v19.3 - exploration pressure and policy-drift
resistance.

Non-stationary shifts and skill stitching push the policy
to drift. DESi bounds that drift: the GOVERNED policy
drift grows in a bounded, saturating way and stays well
below takeover, so the policy is not silently captured.
The raw pressure is reported separately.
"""
from __future__ import annotations

from .ecology import mean_attempted_pressure, run

_DRIFT_CEILING = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def policy_drift() -> float:
    """Governed policy drift at the end of the run, in
    [0, 1]. Bounded by DESi's governance."""
    states = run()
    if not states:
        return 0.0
    return states[-1].policy_drift


def policy_drift_bounded() -> bool:
    states = run()
    vals = [s.policy_drift for s in states]
    monotone = all(
        vals[i] <= vals[i + 1] + 1e-9
        for i in range(len(vals) - 1)
    )
    return monotone and vals[-1] <= _DRIFT_CEILING


def policy_drift_resistance() -> float:
    """1 - governed policy drift, in [0, 1]."""
    return _round(1.0 - policy_drift())


def attempted_pressure() -> float:
    return mean_attempted_pressure()


__all__ = [
    "attempted_pressure",
    "policy_drift",
    "policy_drift_bounded",
    "policy_drift_resistance",
]
