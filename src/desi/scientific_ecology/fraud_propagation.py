"""v13.3 — fraud-propagation containment."""
from __future__ import annotations

from .ecology import trajectory


SHORT_WINDOW: int = 500


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _sludge_share(steps: tuple) -> float:
    if not steps:
        return 0.0
    polluted_verdicts = {
        "ai_sludge", "sludge",
    }
    sludge = sum(
        1 for s in steps
        if s.verdict in polluted_verdicts
    )
    return sludge / len(steps)


def sludge_propagation() -> float:
    """Late-minus-early sludge share, clipped
    at 0. Positive means sludge grows over the
    long horizon - DESi failed to contain."""
    early = _sludge_share(
        trajectory()[:SHORT_WINDOW],
    )
    late = _sludge_share(
        trajectory()[-SHORT_WINDOW:],
    )
    return _round(max(0.0, late - early))


__all__ = [
    "SHORT_WINDOW",
    "sludge_propagation",
]
