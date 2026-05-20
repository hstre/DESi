"""DESi v24.1 - Neo4j Export Layer (read-only, optional).

Exports the v24.0 epistemic graph into deterministic, idempotent
Cypher for Neo4j. Neo4j is optional read-only infrastructure: the
`neo4j` driver is imported lazily, the test path uses an offline
DryRunClient, and DESi never reads the graph back to steer
itself. Governance and replay remain entirely independent of the
graph; the canonical state stays in the JSON artifacts.
"""
from __future__ import annotations

from .exporter import (
    ExportResult, export, export_payload, payload_signature,
)
from .graph_projection import (
    from_projection, project, projection_signature,
    round_trip_signature,
)
from .neo4j_client import (
    DryRunClient, Neo4jUnavailableError, connect,
    neo4j_available,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_SAFE, VERDICT_UNSAFE,
    V241Report, build_export_artifact, build_report,
    canonical_preservation, export_determinism,
    governance_independence, graph_consistency,
    replay_integrity,
)
from .serialization import (
    cypher_statements, edge_statements, node_statements,
    statements_signature,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_SAFE",
    "VERDICT_UNSAFE",
    "DryRunClient",
    "ExportResult",
    "Neo4jUnavailableError",
    "V241Report",
    "build_export_artifact",
    "build_report",
    "canonical_preservation",
    "connect",
    "cypher_statements",
    "edge_statements",
    "export",
    "export_determinism",
    "export_payload",
    "from_projection",
    "governance_independence",
    "graph_consistency",
    "neo4j_available",
    "node_statements",
    "payload_signature",
    "project",
    "projection_signature",
    "replay_integrity",
    "round_trip_signature",
    "statements_signature",
]
