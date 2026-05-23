"""v27.1 - optional Neo4j projection.

Projects the claim graph into deterministic, idempotent Cypher.
Neo4j stays read-only, optional infrastructure: the driver is
imported lazily (reusing the v24.1 client), the test path uses an
offline DryRunClient, and DESi reads nothing back from the graph.
"""
from __future__ import annotations

import hashlib
import json

from desi.epistemic_graph_export import (
    DryRunClient, Neo4jUnavailableError, connect, neo4j_available,
)

from .graph_builder import edges, nodes


def _esc(s: str) -> str:
    return json.dumps(s, ensure_ascii=False, sort_keys=True)


def node_statement(node) -> str:
    return (
        f"MERGE (n:`{node.node_type}` "
        f"{{node_id: {_esc(node.node_id)}}}) "
        f"SET n.label = {_esc(node.label)}"
    )


def edge_statement(edge) -> str:
    return (
        f"MATCH (a {{node_id: {_esc(edge.source)}}}), "
        f"(b {{node_id: {_esc(edge.target)}}}) "
        f"MERGE (a)-[:`{edge.edge_type}`]->(b)"
    )


def cypher_statements() -> tuple[str, ...]:
    return (
        tuple(node_statement(n) for n in nodes())
        + tuple(edge_statement(e) for e in edges())
    )


def statements_signature() -> str:
    return hashlib.sha256(
        "\n".join(cypher_statements()).encode("utf-8"),
    ).hexdigest()


def project(client: DryRunClient | None = None) -> int:
    """Run the projection against an offline client (default) or
    a provided one. Returns the statement count. Read-only from
    DESi's side: it only writes provenance, never reads back."""
    target = client if client is not None else DryRunClient()
    stmts = cypher_statements()
    for s in stmts:
        target.run(s)
    return len(stmts)


__all__ = [
    "DryRunClient",
    "Neo4jUnavailableError",
    "connect",
    "cypher_statements",
    "edge_statement",
    "neo4j_available",
    "node_statement",
    "project",
    "statements_signature",
]
