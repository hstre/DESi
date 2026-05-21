"""v27.1 - claim-graph node and edge taxonomy.

Closed node and edge types for the research claim graph, plus
the allowed (source_type, edge_type, target_type) triples. The
graph is read-only epistemic structure: it ranks nothing,
prioritises nothing and hides no optimisation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    PAPER = "Paper"
    CLAIM = "Claim"
    METHOD = "Method"
    METRIC = "Metric"
    DATASET = "Dataset"
    LIMITATION = "Limitation"
    OPEN_QUESTION = "OpenQuestion"
    AUTHOR = "Author"


class EdgeType(Enum):
    CLAIMS = "CLAIMS"
    SUPPORTS = "SUPPORTS"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    EXTENDS = "EXTENDS"
    REUSES_METHOD = "REUSES_METHOD"
    REUSES_METRIC = "REUSES_METRIC"
    LEAVES_OPEN = "LEAVES_OPEN"
    LIMITED_BY = "LIMITED_BY"
    DERIVED_FROM = "DERIVED_FROM"


NODE_TYPES: tuple[str, ...] = tuple(t.value for t in NodeType)
EDGE_TYPES: tuple[str, ...] = tuple(t.value for t in EdgeType)
_NODE_VALUES: frozenset[str] = frozenset(NODE_TYPES)
_EDGE_VALUES: frozenset[str] = frozenset(EDGE_TYPES)

_N = NodeType
_E = EdgeType

_ALLOWED_TRIPLES: tuple[tuple[str, str, str], ...] = (
    (_N.PAPER.value, _E.CLAIMS.value, _N.CLAIM.value),
    (_N.AUTHOR.value, _E.CLAIMS.value, _N.CLAIM.value),
    (_N.CLAIM.value, _E.SUPPORTS.value, _N.CLAIM.value),
    (_N.CLAIM.value, _E.CONFLICTS_WITH.value, _N.CLAIM.value),
    (_N.PAPER.value, _E.EXTENDS.value, _N.PAPER.value),
    (_N.PAPER.value, _E.REUSES_METHOD.value, _N.METHOD.value),
    (_N.PAPER.value, _E.REUSES_METRIC.value, _N.METRIC.value),
    (_N.PAPER.value, _E.LEAVES_OPEN.value, _N.OPEN_QUESTION.value),
    (_N.PAPER.value, _E.LIMITED_BY.value, _N.LIMITATION.value),
    (_N.PAPER.value, _E.DERIVED_FROM.value, _N.DATASET.value),
)


@dataclass(frozen=True)
class Node:
    node_id: str
    node_type: str
    label: str

    def __post_init__(self) -> None:
        if self.node_type not in _NODE_VALUES:
            raise ValueError(f"unknown node_type: {self.node_type}")

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
        }

    def sort_key(self) -> tuple[str, str]:
        return (self.node_type, self.node_id)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    edge_type: str

    def __post_init__(self) -> None:
        if self.edge_type not in _EDGE_VALUES:
            raise ValueError(f"unknown edge_type: {self.edge_type}")

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type,
        }

    def sort_key(self) -> tuple[str, str, str]:
        return (self.edge_type, self.source, self.target)


def allowed_triples() -> tuple[tuple[str, str, str], ...]:
    return _ALLOWED_TRIPLES


def is_valid_triple(s: str, e: str, t: str) -> bool:
    return (s, e, t) in _ALLOWED_TRIPLES


__all__ = [
    "EDGE_TYPES",
    "NODE_TYPES",
    "Edge",
    "EdgeType",
    "Node",
    "NodeType",
    "allowed_triples",
    "is_valid_triple",
]
