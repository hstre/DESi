"""DESi v27.1 - Claim Graph & Neo4j Integration (read-only).

Renders the harvested research corpus as an explicit read-only
epistemic claim graph: papers, claims, methods, metrics,
datasets, authors, limitations and open questions as nodes, and
their relations as edges. Interweavings, conflicts and open
research spaces are made visible. Neo4j is optional read-only
infrastructure - offline in tests, lazy driver otherwise - and
DESi reads nothing back and ranks nothing.
"""
from __future__ import annotations

from .graph_builder import (
    determinism_signatures, edges, edges_of_type,
    graph_signature, nodes, nodes_of_type,
)
from .lineage import (
    connected_node_fraction, has_cycle, has_dangling_edges,
    invalid_edges, out_edges,
)
from .neo4j_projection import (
    DryRunClient, Neo4jUnavailableError, connect,
    cypher_statements, neo4j_available, project,
    statements_signature,
)
from .relations import (
    EDGE_TYPES, NODE_TYPES, Edge, EdgeType, Node, NodeType,
    allowed_triples, is_valid_triple,
)
from .report import (
    REPORT_VERDICTS, VERDICT_GRAPHED, VERDICT_HALT,
    VERDICT_PARTIAL, V271Report, build_graph_artifact,
    build_report, conflict_visibility, graph_connectivity,
    lineage_integrity, open_problem_visibility, replay_stability,
)


__all__ = [
    "EDGE_TYPES",
    "NODE_TYPES",
    "REPORT_VERDICTS",
    "VERDICT_GRAPHED",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "DryRunClient",
    "Edge",
    "EdgeType",
    "Neo4jUnavailableError",
    "Node",
    "NodeType",
    "V271Report",
    "allowed_triples",
    "build_graph_artifact",
    "build_report",
    "conflict_visibility",
    "connect",
    "connected_node_fraction",
    "cypher_statements",
    "determinism_signatures",
    "edges",
    "edges_of_type",
    "graph_connectivity",
    "graph_signature",
    "has_cycle",
    "has_dangling_edges",
    "invalid_edges",
    "is_valid_triple",
    "lineage_integrity",
    "neo4j_available",
    "nodes",
    "nodes_of_type",
    "open_problem_visibility",
    "out_edges",
    "project",
    "replay_stability",
    "statements_signature",
]
