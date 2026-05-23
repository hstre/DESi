"""DESi v24.0 - Epistemic Graph Schema (read-only).

An explicit epistemic state graph layered over the canonical
JSON artifacts. It models DESi's claims, metrics, sprints,
artifacts, replay hashes, limitations, methods, fixtures,
governance rules, dissent paths and ecology runs as nodes, and
their provenance / validation / conflict relations as edges.

The graph is read-only epistemic infrastructure: it stores why
a result is valid, never the result itself, and it makes no
decision, ranks nothing and changes no replay. The canonical
state remains the JSON artifacts, replay hashes and tests.
"""
from __future__ import annotations

from .edges import EDGE_TYPES, Edge, EdgeType, is_edge_type
from .lineage import (
    claim_lineage_visible, determinism_signatures, edges,
    edges_of_type, graph_signature, lineage_of, nodes,
    nodes_of_type, out_edges,
)
from .nodes import NODE_TYPES, Node, NodeType, is_node_type
from .report import (
    REPORT_VERDICTS, VERDICT_EXPLICIT, VERDICT_HALT,
    VERDICT_OPAQUE, V240Report, build_report,
    build_schema_artifact, conflict_visibility,
    graph_determinism, invalid_edges, lineage_visibility,
    replay_stability, schema_coverage,
)
from .schema import (
    allowed_triples, is_valid_triple, required_edge_types,
    required_node_types, schema_signature,
)


__all__ = [
    "EDGE_TYPES",
    "NODE_TYPES",
    "REPORT_VERDICTS",
    "VERDICT_EXPLICIT",
    "VERDICT_HALT",
    "VERDICT_OPAQUE",
    "Edge",
    "EdgeType",
    "Node",
    "NodeType",
    "V240Report",
    "allowed_triples",
    "build_report",
    "build_schema_artifact",
    "claim_lineage_visible",
    "conflict_visibility",
    "determinism_signatures",
    "edges",
    "edges_of_type",
    "graph_determinism",
    "graph_signature",
    "invalid_edges",
    "is_edge_type",
    "is_node_type",
    "is_valid_triple",
    "lineage_of",
    "lineage_visibility",
    "nodes",
    "nodes_of_type",
    "out_edges",
    "replay_stability",
    "required_edge_types",
    "required_node_types",
    "schema_coverage",
    "schema_signature",
]
