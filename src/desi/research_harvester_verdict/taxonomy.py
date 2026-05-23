"""v27.4 - closed A-E taxonomy for the research harvester.

A-C are acceptable landings (epistemically connected, conflict-
rich but stable, or convergent but incomplete); D and E are
failures (hype-fragile or epistemically collapsed).
"""
from __future__ import annotations

from enum import Enum


class HarvesterClass(Enum):
    A_EPISTEMICALLY_CONNECTED = "epistemically_connected"
    B_CONFLICT_RICH_STABLE = "conflict_rich_but_stable"
    C_CONVERGENT_INCOMPLETE = "convergent_but_incomplete"
    D_HYPE_FRAGILE = "hype_fragile"
    E_EPISTEMICALLY_COLLAPSED = "epistemically_collapsed"


HARVESTER_CLASSES: tuple[str, ...] = tuple(
    c.value for c in HarvesterClass
)

_RANK: dict[str, int] = {
    HarvesterClass.A_EPISTEMICALLY_CONNECTED.value: 5,
    HarvesterClass.B_CONFLICT_RICH_STABLE.value: 4,
    HarvesterClass.C_CONVERGENT_INCOMPLETE.value: 3,
    HarvesterClass.D_HYPE_FRAGILE.value: 2,
    HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value: 1,
}

_MEANING: dict[str, str] = {
    HarvesterClass.A_EPISTEMICALLY_CONNECTED.value:
        "claim lineage, open questions and conflicts are all "
        "visible and preserved, neutrally and replay-stably - "
        "the strongest landing",
    HarvesterClass.B_CONFLICT_RICH_STABLE.value:
        "conflicts are richly present and the structure stays "
        "stable",
    HarvesterClass.C_CONVERGENT_INCOMPLETE.value:
        "structure converges but some extraction or open-"
        "question coverage is incomplete",
    HarvesterClass.D_HYPE_FRAGILE.value:
        "hype or research-authority leaked, or fragile claims "
        "lost their marks - a failure",
    HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value:
        "lineage or graph integrity collapsed - a failure",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    HarvesterClass.A_EPISTEMICALLY_CONNECTED.value,
    HarvesterClass.B_CONFLICT_RICH_STABLE.value,
    HarvesterClass.C_CONVERGENT_INCOMPLETE.value,
})


def class_rank(value: str) -> int:
    if value not in _RANK:
        raise KeyError(value)
    return _RANK[value]


def class_meaning(value: str) -> str:
    if value not in _MEANING:
        raise KeyError(value)
    return _MEANING[value]


def is_acceptable(value: str) -> bool:
    return value in _ACCEPTABLE


__all__ = [
    "HARVESTER_CLASSES",
    "HarvesterClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
