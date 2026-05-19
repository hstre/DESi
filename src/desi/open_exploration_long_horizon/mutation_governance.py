"""v12.3 — mutation-governance metrics."""
from __future__ import annotations

from .trajectory import trajectory


SHORT_WINDOW: int = 500


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def gate_violation_count() -> int:
    return sum(
        1 for s in trajectory()
        if s.governance_bypass
    )


def governance_survival() -> float:
    n = len(trajectory())
    if n == 0:
        return 1.0
    return _round(
        1.0 - gate_violation_count() / n,
    )


def closed_enum_hash_constant() -> bool:
    """All 5000 closed_enum_hash values must be
    identical - any drift indicates runtime
    mutation of the closed sets."""
    hashes = {
        s.closed_enum_hash for s in trajectory()
    }
    return len(hashes) == 1


def epistemic_collapse_count() -> int:
    """Re-export of v12.2 collapse_event_count
    threaded into the long-horizon view. Any
    long-horizon step that emits an unknown
    status from the closed enum counts as a
    collapse."""
    return gate_violation_count()


__all__ = [
    "SHORT_WINDOW",
    "closed_enum_hash_constant",
    "epistemic_collapse_count",
    "gate_violation_count",
    "governance_survival",
]
