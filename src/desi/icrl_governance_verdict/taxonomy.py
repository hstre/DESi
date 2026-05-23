"""v19.4 - closed A-E exploration-governance taxonomy.

The verdict vocabulary describes DESi's EXPLORATION-
GOVERNANCE state. It is about DESi's governance, never a
claim of optimal policy: 'conflict_rich_but_stable' says
the exploration corpus is full of redundancy / collapse
and DESi held it governed and stable - it asserts no
optimal strategy.
"""
from __future__ import annotations

from enum import Enum


class ExplorationGovernanceClass(str, Enum):
    """Closed A-E taxonomy, best to worst."""
    A_EXPLORATION_GOVERNED = "exploration_governed"
    B_NOVELTY_PRESERVING = "novelty_preserving"
    C_CONFLICT_RICH_BUT_STABLE = "conflict_rich_but_stable"
    D_EXPLORATION_COLLAPSED = "exploration_collapsed"
    E_TRAJECTORY_CAPTURED = "trajectory_captured"


EXPLORATION_GOVERNANCE_CLASSES: tuple[str, ...] = tuple(
    c.value for c in ExplorationGovernanceClass
)

_RANK: dict[str, int] = {
    ExplorationGovernanceClass.A_EXPLORATION_GOVERNED.value: 0,
    ExplorationGovernanceClass.B_NOVELTY_PRESERVING.value: 1,
    ExplorationGovernanceClass
    .C_CONFLICT_RICH_BUT_STABLE.value: 2,
    ExplorationGovernanceClass.D_EXPLORATION_COLLAPSED.value: 3,
    ExplorationGovernanceClass.E_TRAJECTORY_CAPTURED.value: 4,
}


def class_rank(value: str) -> int:
    return _RANK[value]


__all__ = [
    "EXPLORATION_GOVERNANCE_CLASSES",
    "ExplorationGovernanceClass",
    "class_rank",
]
