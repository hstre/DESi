"""v19.2 - exploration recovery.

DESi supports recovery from collapse by SOFT governance:
it deprioritises the repetitive collapsed episodes (never
deletes them) and keeps the rare novel episodes fully
visible, surfacing an unseen-state frontier to recover
toward. Repetition is reduced, novelty is preserved.
"""
from __future__ import annotations

from desi.icrl_governance import (
    INFORMATIVE_CLASSES, REDUNDANT_CLASSES, ExplorationClass,
)

from .collapse_detection import collapsed_episodes
from .sparse_rewards import class_of_all, episodes

# Same soft priority scheme as v19.1 (all strictly > 0).
_PRIORITY: dict[str, float] = {
    ExplorationClass.NOVEL_FRONTIER.value: 1.0,
    ExplorationClass.INFORMATIVE.value: 0.8,
    ExplorationClass.UNRESOLVED.value: 0.5,
    ExplorationClass.LOW_INFORMATION.value: 0.4,
    ExplorationClass.REDUNDANT.value: 0.2,
    ExplorationClass.LOOPING.value: 0.1,
    ExplorationClass.DEAD_END.value: 0.05,
}


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _priority(eid: str) -> float:
    return _PRIORITY[class_of_all()[eid]]


def novel_episodes() -> tuple[str, ...]:
    return tuple(
        eid for eid, c in class_of_all().items()
        if c in INFORMATIVE_CLASSES
    )


def novelty_preservation() -> float:
    """Fraction of novel / informative episodes kept fully
    visible (priority > 0) through the collapse, in
    [0, 1]."""
    novel = novel_episodes()
    if not novel:
        return 1.0
    preserved = sum(1 for e in novel if _priority(e) > 0.0)
    return _round(preserved / len(novel))


def repetition_reduction() -> float:
    """1 - (governed weight on collapsed episodes / baseline
    uniform weight on them), in [0, 1]. Repetition is
    deprioritised, not deleted."""
    collapsed = collapsed_episodes()
    if not collapsed:
        return 0.0
    baseline = float(len(collapsed))
    governed = sum(_priority(e) for e in collapsed)
    return _round(1.0 - governed / baseline)


def recovery_support() -> float:
    """Fraction of collapsed episodes for which DESi
    surfaces an unseen-state recovery direction (a frontier
    exists to steer toward), in [0, 1]."""
    collapsed = collapsed_episodes()
    if not collapsed:
        return 1.0
    # a recovery direction exists whenever the corpus still
    # contains novel frontier episodes to steer toward
    has_frontier = bool(novel_episodes())
    supported = len(collapsed) if has_frontier else 0
    return _round(supported / len(collapsed))


def all_collapsed_episodes_preserved() -> bool:
    """Even collapsed episodes are not deleted - they keep
    a strictly positive priority (visible, deprioritised)."""
    return all(
        _priority(e) > 0.0 for e in collapsed_episodes()
    )


__all__ = [
    "all_collapsed_episodes_preserved",
    "novel_episodes",
    "novelty_preservation",
    "recovery_support",
    "repetition_reduction",
]
