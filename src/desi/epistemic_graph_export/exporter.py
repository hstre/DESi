"""v24.1 - export orchestration.

Drives the deterministic, replay-safe export of the v24.0 graph.
By default the export targets an offline DryRunClient (no Neo4j
required); a real driver can be supplied in environments where
the `neo4j` package and a service container are available. The
export only writes; it never reads the graph back into DESi.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .graph_projection import project, round_trip_signature
from .neo4j_client import DryRunClient
from .serialization import (
    cypher_statements, statements_signature,
)


@dataclass(frozen=True)
class ExportResult:
    node_count: int
    edge_count: int
    statement_count: int
    signature: str

    def to_dict(self) -> dict[str, object]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "statement_count": self.statement_count,
            "signature": self.signature,
        }


def export(client: DryRunClient | None = None) -> ExportResult:
    """Serialize the graph and run the statements against the
    given client (an offline DryRunClient by default). Returns a
    deterministic summary; does not mutate the source graph."""
    stmts = cypher_statements()
    target = client if client is not None else DryRunClient()
    for s in stmts:
        target.run(s)
    proj = project()
    nodes_total = sum(
        len(v) for v in proj["nodes_by_type"].values()  # type: ignore[union-attr]
    )
    edges_total = sum(
        len(v) for v in proj["edges_by_type"].values()  # type: ignore[union-attr]
    )
    return ExportResult(
        node_count=nodes_total,
        edge_count=edges_total,
        statement_count=len(stmts),
        signature=statements_signature(),
    )


def export_payload() -> dict[str, object]:
    """The full deterministic export payload (projection +
    Cypher), suitable for reproducible re-import."""
    return {
        "projection": project(),
        "cypher": list(cypher_statements()),
        "statements_signature": statements_signature(),
        "round_trip_signature": round_trip_signature(),
    }


def payload_signature() -> str:
    return hashlib.sha256(
        "\n".join(cypher_statements()).encode("utf-8"),
    ).hexdigest()


__all__ = [
    "ExportResult",
    "export",
    "export_payload",
    "payload_signature",
]
