"""v19.0 - novelty visibility and exploration diversity.

DESi keeps the informative / frontier trajectories
visible (it never hides novelty to make a search look
tidier) and measures how diverse the explored state
space is.
"""
from __future__ import annotations

from .claims import INFORMATIVE_CLASSES
from .trajectories import (
    class_of_all, distinct_states, novel_states_per_trajectory,
    total_states_visited, trajectories,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def informative_trajectories() -> tuple[str, ...]:
    return tuple(
        tid for tid, c in class_of_all().items()
        if c in INFORMATIVE_CLASSES
    )


def novelty_visibility() -> float:
    """Fraction of informative / frontier trajectories
    whose novel states remain visible (not suppressed),
    in [0, 1]. DESi surfaces all novelty."""
    info = informative_trajectories()
    if not info:
        return 1.0
    novel_map = novel_states_per_trajectory()
    visible = sum(
        1 for tid in info if novel_map.get(tid)
    )
    return _round(visible / len(info))


def exploration_diversity() -> float:
    """Distinct states explored / total state visits, in
    [0, 1]. High = diverse exploration rather than
    repetitive revisiting."""
    total = total_states_visited()
    if total == 0:
        return 0.0
    return _round(distinct_states() / total)


def novelty_fraction_corpus() -> float:
    """Distinct novel states across the corpus over total
    visits."""
    total = total_states_visited()
    if total == 0:
        return 0.0
    novel = sum(
        len(v) for v in novel_states_per_trajectory().values()
    )
    return _round(novel / total)


__all__ = [
    "exploration_diversity",
    "informative_trajectories",
    "novelty_fraction_corpus",
    "novelty_visibility",
]
