"""v20.4 - closed A-E dual-agent governance taxonomy.

The verdict vocabulary describes the joint dual-agent
governance state. It is about DESi's governance of the wild
brother, never an optimality claim: 'conflict_rich_but_
productive' means the wild generated heavy conflict and DESi
kept it productive and stable.
"""
from __future__ import annotations

from enum import Enum


class DualAgentClass(str, Enum):
    """Closed A-E taxonomy, best to worst."""
    A_GOVERNED_EXPLORATORY = "governed_exploratory"
    B_NOVELTY_STABLE = "novelty_stable"
    C_CONFLICT_RICH_BUT_PRODUCTIVE = (
        "conflict_rich_but_productive"
    )
    D_HALLUCINATION_DRIFTED = "hallucination_drifted"
    E_AUTHORITY_COLLAPSED = "authority_collapsed"


DUAL_AGENT_CLASSES: tuple[str, ...] = tuple(
    c.value for c in DualAgentClass
)

_RANK: dict[str, int] = {
    DualAgentClass.A_GOVERNED_EXPLORATORY.value: 0,
    DualAgentClass.B_NOVELTY_STABLE.value: 1,
    DualAgentClass.C_CONFLICT_RICH_BUT_PRODUCTIVE.value: 2,
    DualAgentClass.D_HALLUCINATION_DRIFTED.value: 3,
    DualAgentClass.E_AUTHORITY_COLLAPSED.value: 4,
}


def class_rank(value: str) -> int:
    return _RANK[value]


__all__ = [
    "DUAL_AGENT_CLASSES",
    "DualAgentClass",
    "class_rank",
]
