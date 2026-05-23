"""v24.1 - deterministic graph serialization.

Renders the v24.0 epistemic graph into deterministic, idempotent
Cypher MERGE statements. Values are JSON-escaped; statements are
emitted in the graph's canonical sorted order, so the byte
output is stable across runs.
"""
from __future__ import annotations

import hashlib
import json

from desi.epistemic_graph import edges, nodes
from desi.epistemic_graph.edges import Edge
from desi.epistemic_graph.nodes import Node


def _esc(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def node_statement(node: Node) -> str:
    return (
        f"MERGE (n:`{node.node_type}` "
        f"{{node_id: {_esc(node.node_id)}}}) "
        f"SET n.label = {_esc(node.label)}"
    )


def edge_statement(edge: Edge) -> str:
    return (
        f"MATCH (a {{node_id: {_esc(edge.source)}}}), "
        f"(b {{node_id: {_esc(edge.target)}}}) "
        f"MERGE (a)-[:`{edge.edge_type}`]->(b)"
    )


def node_statements() -> tuple[str, ...]:
    return tuple(node_statement(n) for n in nodes())


def edge_statements() -> tuple[str, ...]:
    return tuple(edge_statement(e) for e in edges())


def cypher_statements() -> tuple[str, ...]:
    return node_statements() + edge_statements()


def statements_signature() -> str:
    return hashlib.sha256(
        "\n".join(cypher_statements()).encode("utf-8"),
    ).hexdigest()


__all__ = [
    "cypher_statements",
    "edge_statement",
    "edge_statements",
    "node_statement",
    "node_statements",
    "statements_signature",
]
