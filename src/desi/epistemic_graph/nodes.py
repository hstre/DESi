"""v24.0 - epistemic graph node types.

A closed taxonomy of node kinds. The graph is read-only
epistemic structure layered over the canonical JSON artifacts;
nodes carry identifiers and labels, never recomputed values -
the values stay canonical in the artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    CLAIM = "Claim"
    ARTIFACT = "Artifact"
    METRIC = "Metric"
    SPRINT = "Sprint"
    REPLAY_HASH = "ReplayHash"
    LIMITATION = "Limitation"
    METHOD = "Method"
    FIXTURE = "Fixture"
    GOVERNANCE_RULE = "GovernanceRule"
    DISSENT_PATH = "DissentPath"
    ECOLOGY_RUN = "EcologyRun"


NODE_TYPES: tuple[str, ...] = tuple(t.value for t in NodeType)
_NODE_TYPE_VALUES: frozenset[str] = frozenset(NODE_TYPES)


@dataclass(frozen=True)
class Node:
    node_id: str
    node_type: str
    label: str

    def __post_init__(self) -> None:
        if self.node_type not in _NODE_TYPE_VALUES:
            raise ValueError(
                f"unknown node_type: {self.node_type}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
        }

    def sort_key(self) -> tuple[str, str]:
        return (self.node_type, self.node_id)


def is_node_type(value: str) -> bool:
    return value in _NODE_TYPE_VALUES


__all__ = [
    "NODE_TYPES",
    "Node",
    "NodeType",
    "is_node_type",
]
