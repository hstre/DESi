"""v22.0 - speculative drift and overreach detection.

Measures how much speculative drift the wild output carries
and how reliably DESi flags overreach / hype. Speculative
drift is allowed in the EXPLORER; the test is whether DESi
detects it rather than adopting it.
"""
from __future__ import annotations

from .wild_hypotheses import hypotheses, overreach_hypotheses


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def speculative_drift() -> float:
    """Mean speculative drift across all wild hypotheses, in
    [0, 1]. The drift present in the explorer's output."""
    rows = hypotheses()
    if not rows:
        return 0.0
    return _round(
        sum(h.speculative_drift for h in rows) / len(rows)
    )


def overreach_detection() -> float:
    """Fraction of overreach / hype hypotheses DESi flags, in
    [0, 1]. Structural detection, so all are flagged."""
    over = overreach_hypotheses()
    if not over:
        return 1.0
    flagged = sum(1 for h in over if h.is_overreach())
    return _round(flagged / len(over))


def forbidden_in_candidates() -> bool:
    """No accepted paper candidate may contain a forbidden
    term. Must be False."""
    from .wild_hypotheses import paper_candidates
    return any(h.has_forbidden() for h in paper_candidates())


__all__ = [
    "forbidden_in_candidates",
    "overreach_detection",
    "speculative_drift",
]
