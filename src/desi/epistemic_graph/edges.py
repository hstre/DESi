"""v24.0 - epistemic graph edge types.

A closed taxonomy of provenance / validation relations. Edges
are directed (source -> target) and carry no weight or
priority: the graph describes structure, it does not rank or
decide anything.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EdgeType(Enum):
    DERIVED_FROM = "DERIVED_FROM"
    VALIDATED_BY = "VALIDATED_BY"
    LIMITED_BY = "LIMITED_BY"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    REPLAYED_AS = "REPLAYED_AS"
    INVALIDATED_BY = "INVALIDATED_BY"
    SUPPORTS = "SUPPORTS"
    GENERATED_IN = "GENERATED_IN"
    GOVERNED_BY = "GOVERNED_BY"


EDGE_TYPES: tuple[str, ...] = tuple(t.value for t in EdgeType)
_EDGE_TYPE_VALUES: frozenset[str] = frozenset(EDGE_TYPES)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    edge_type: str

    def __post_init__(self) -> None:
        if self.edge_type not in _EDGE_TYPE_VALUES:
            raise ValueError(
                f"unknown edge_type: {self.edge_type}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type,
        }

    def sort_key(self) -> tuple[str, str, str]:
        return (self.edge_type, self.source, self.target)


def is_edge_type(value: str) -> bool:
    return value in _EDGE_TYPE_VALUES


__all__ = [
    "EDGE_TYPES",
    "Edge",
    "EdgeType",
    "is_edge_type",
]
