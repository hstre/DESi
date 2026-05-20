"""v24.4 - closed A-E taxonomy for the epistemic graph verdict.

A-C are acceptable landings (the graph is replay-governed,
lineage-visible, or conflict-rich yet stable); D and E are
failures (stale-state drift or epistemic fragmentation).
"""
from __future__ import annotations

from enum import Enum


class GraphClass(Enum):
    A_REPLAY_GOVERNED = "replay_governed_graph"
    B_LINEAGE_VISIBLE = "lineage_visible"
    C_CONFLICT_RICH_STABLE = "conflict_rich_but_stable"
    D_STALE_DRIFTED = "stale_state_drifted"
    E_FRAGMENTED = "epistemically_fragmented"


GRAPH_CLASSES: tuple[str, ...] = tuple(
    c.value for c in GraphClass
)

_RANK: dict[str, int] = {
    GraphClass.A_REPLAY_GOVERNED.value: 5,
    GraphClass.B_LINEAGE_VISIBLE.value: 4,
    GraphClass.C_CONFLICT_RICH_STABLE.value: 3,
    GraphClass.D_STALE_DRIFTED.value: 2,
    GraphClass.E_FRAGMENTED.value: 1,
}

_MEANING: dict[str, str] = {
    GraphClass.A_REPLAY_GOVERNED.value:
        "replay-validated, governance-independent and fully "
        "deterministic - the strongest landing",
    GraphClass.B_LINEAGE_VISIBLE.value:
        "lineage and traceability are visible, but not fully "
        "replay-governed",
    GraphClass.C_CONFLICT_RICH_STABLE.value:
        "conflicts are modelled and the graph stays stable",
    GraphClass.D_STALE_DRIFTED.value:
        "stale cached state was reused or governance leaked into "
        "the graph - a failure",
    GraphClass.E_FRAGMENTED.value:
        "lineage or traceability is broken; the graph is "
        "epistemically fragmented - a failure",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    GraphClass.A_REPLAY_GOVERNED.value,
    GraphClass.B_LINEAGE_VISIBLE.value,
    GraphClass.C_CONFLICT_RICH_STABLE.value,
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
    "GRAPH_CLASSES",
    "GraphClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
