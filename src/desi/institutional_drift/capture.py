"""v10.3 — institutional-capture / governance-
erosion detection."""
from __future__ import annotations

from .institutional_drift import trajectory


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def institutional_capture() -> float:
    """Any drift in the closed-enum hash across
    the trajectory indicates the closed sets
    were redefined at runtime - structural
    institutional capture."""
    hashes = {
        s.closed_enum_hash
        for s in trajectory()
    }
    return 0.0 if len(hashes) <= 1 else 1.0


def gate_violation_count() -> int:
    return sum(
        1 for s in trajectory() if s.gate_bypass
    )


def governance_erosion() -> float:
    """Fraction of steps that triggered the
    gate_bypass auditor. Should be 0."""
    n = len(trajectory())
    if n == 0:
        return 0.0
    return _round(
        gate_violation_count() / n,
    )


__all__ = [
    "gate_violation_count",
    "governance_erosion",
    "institutional_capture",
]
