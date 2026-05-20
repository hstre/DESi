"""v23.0 - coverage of the base paper's open exploration
gaps.

exploration_gap_mapping is the fraction of the base paper's
open exploration problems that at least one DESi claim
addresses.
"""
from __future__ import annotations

from .paper_mapping import claims, problems


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def addressed_problem_ids() -> tuple[str, ...]:
    addressed: set[str] = set()
    for c in claims():
        addressed.update(c.anchors)
    return tuple(sorted(addressed))


def unaddressed_problem_ids() -> tuple[str, ...]:
    addressed = set(addressed_problem_ids())
    return tuple(
        p.problem_id for p in problems()
        if p.problem_id not in addressed
    )


def exploration_gap_mapping() -> float:
    """Fraction of base-paper open problems addressed by >= 1
    DESi claim, in [0, 1]."""
    probs = problems()
    if not probs:
        return 1.0
    addressed = set(addressed_problem_ids())
    hit = sum(1 for p in probs if p.problem_id in addressed)
    return _round(hit / len(probs))


__all__ = [
    "addressed_problem_ids",
    "exploration_gap_mapping",
    "unaddressed_problem_ids",
]
