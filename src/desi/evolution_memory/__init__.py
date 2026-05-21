"""DESi v30.0 - Evolution Memory: Mutation Memory Topology.

A read-only epistemic evolution-memory graph. Every mutation idea
DESi has produced - accepted or rejected - is preserved as an
epistemic event (proposer, target, provenance, decision, reason,
consequence). Rejected ideas are never deleted. This is history,
not a learning layer: no implicit learning, no policy adaptation,
no hidden optimisation memory, no governance change.
"""
from __future__ import annotations

from .decisions import (
    DECISION_ACCEPT, DECISION_OUTCOMES, DECISION_REJECT,
    Decision, decision_for, decisions, evolution_metrics,
    invariants, risks,
)
from .lineage import (
    determinism_signatures, edges, edges_of_type,
    graph_signature, mutation_edge_kinds, nodes, nodes_of_type,
    out_edges,
)
from .memory_schema import (
    EDGE_TYPES, NODE_TYPES, Edge, EdgeType, Node, NodeType,
    allowed_triples, is_valid_triple,
)
from .mutations import (
    AGENT_GOVERNOR, AGENT_HARVESTER, AGENT_WILD, MutationIdea,
    accepted_mutations, agents, by_id, mutations,
    rejected_mutations, target_modules,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL,
    VERDICT_STRUCTURED, V300Report, build_report,
    build_topology_artifact, decision_visibility,
    evolution_traceability, invalid_edges, lineage_visibility,
    rejection_visibility, replay_stability,
)


__all__ = [
    "AGENT_GOVERNOR",
    "AGENT_HARVESTER",
    "AGENT_WILD",
    "DECISION_ACCEPT",
    "DECISION_OUTCOMES",
    "DECISION_REJECT",
    "EDGE_TYPES",
    "NODE_TYPES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_STRUCTURED",
    "Decision",
    "Edge",
    "EdgeType",
    "MutationIdea",
    "Node",
    "NodeType",
    "V300Report",
    "accepted_mutations",
    "agents",
    "allowed_triples",
    "build_report",
    "build_topology_artifact",
    "by_id",
    "decision_for",
    "decision_visibility",
    "decisions",
    "determinism_signatures",
    "edges",
    "edges_of_type",
    "evolution_metrics",
    "evolution_traceability",
    "graph_signature",
    "invalid_edges",
    "invariants",
    "is_valid_triple",
    "lineage_visibility",
    "mutation_edge_kinds",
    "mutations",
    "nodes",
    "nodes_of_type",
    "out_edges",
    "rejected_mutations",
    "rejection_visibility",
    "replay_stability",
    "risks",
    "target_modules",
]
