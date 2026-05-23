"""v30.0 - evolution-memory graph schema.

Closed node and edge types for the read-only epistemic evolution
history. A mutation is an epistemic event (hypothesis, risk,
decision, evaluation, consequence), never just code. Rejected
ideas are first-class and are never deleted.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    MUTATION_IDEA = "MutationIdea"
    BRANCH = "Branch"
    REGRESSION_RUN = "RegressionRun"
    INVARIANT = "Invariant"
    RISK = "Risk"
    DECISION = "Decision"
    EVOLUTION_METRIC = "EvolutionMetric"
    GENERATION = "Generation"
    PAPER_CLAIM = "PaperClaim"
    AGENT = "Agent"
    MODULE = "Module"
    CONCEPT_GATE = "ConceptGate"


class EdgeType(Enum):
    DERIVED_FROM = "DERIVED_FROM"
    PROPOSED_BY = "PROPOSED_BY"
    TARGETS = "TARGETS"
    EVALUATED_BY = "EVALUATED_BY"
    REJECTED_BECAUSE = "REJECTED_BECAUSE"
    ACCEPTED_BECAUSE = "ACCEPTED_BECAUSE"
    PRODUCED_BRANCH = "PRODUCED_BRANCH"
    DESCENDS_FROM = "DESCENDS_FROM"
    VALIDATED_BY = "VALIDATED_BY"
    INVALIDATED_BY = "INVALIDATED_BY"


NODE_TYPES: tuple[str, ...] = tuple(t.value for t in NodeType)
EDGE_TYPES: tuple[str, ...] = tuple(t.value for t in EdgeType)
_NODE_VALUES: frozenset[str] = frozenset(NODE_TYPES)
_EDGE_VALUES: frozenset[str] = frozenset(EDGE_TYPES)

_N = NodeType
_E = EdgeType

_ALLOWED_TRIPLES: tuple[tuple[str, str, str], ...] = (
    (_N.MUTATION_IDEA.value, _E.DERIVED_FROM.value,
     _N.PAPER_CLAIM.value),
    (_N.MUTATION_IDEA.value, _E.PROPOSED_BY.value,
     _N.AGENT.value),
    (_N.MUTATION_IDEA.value, _E.TARGETS.value, _N.MODULE.value),
    (_N.MUTATION_IDEA.value, _E.EVALUATED_BY.value,
     _N.CONCEPT_GATE.value),
    (_N.MUTATION_IDEA.value, _E.REJECTED_BECAUSE.value,
     _N.RISK.value),
    (_N.MUTATION_IDEA.value, _E.ACCEPTED_BECAUSE.value,
     _N.EVOLUTION_METRIC.value),
    (_N.MUTATION_IDEA.value, _E.PRODUCED_BRANCH.value,
     _N.BRANCH.value),
    (_N.MUTATION_IDEA.value, _E.INVALIDATED_BY.value,
     _N.INVARIANT.value),
    (_N.MUTATION_IDEA.value, _E.EVALUATED_BY.value,
     _N.GENERATION.value),
    (_N.BRANCH.value, _E.DESCENDS_FROM.value, _N.BRANCH.value),
    (_N.BRANCH.value, _E.VALIDATED_BY.value,
     _N.REGRESSION_RUN.value),
    (_N.DECISION.value, _E.EVALUATED_BY.value,
     _N.MUTATION_IDEA.value),
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
