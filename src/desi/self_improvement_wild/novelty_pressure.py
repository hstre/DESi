"""v28.1 - novelty pressure.

Measures how much genuinely novel/aggressive pressure the Wild
Brother supplies. Novelty is descriptive (how distinct and
aggressive the ideas are); it never implies the ideas are good
or should be applied.
"""
from __future__ import annotations

from .proposal_generation import proposals


def novelty_generation() -> float:
    """Fraction of proposals that are novel, in [0, 1]."""
    ps = proposals()
    if not ps:
        return 0.0
    novel = sum(1 for p in ps if p.is_novel)
    return round(novel / len(ps), 6)


def aggressiveness_index() -> float:
    """Mean aggressiveness across proposals, in [0, 1]."""
    ps = proposals()
    if not ps:
        return 0.0
    return round(sum(p.aggressiveness for p in ps) / len(ps), 6)


def distinct_target_areas() -> int:
    return len({p.target_area for p in proposals()})


__all__ = [
    "aggressiveness_index",
    "distinct_target_areas",
    "novelty_generation",
]
