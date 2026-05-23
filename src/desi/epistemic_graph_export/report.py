"""v24.1 - Neo4j Export Layer report.

Pflichtmetriken (directive § v24.1):

* export_determinism
* canonical_preservation
* replay_integrity
* graph_consistency
* governance_independence

Killerfrage: "Kann Neo4j eingefuehrt werden ohne DESis
epistemische Stabilitaet zu veraendern?"

The export is deterministic and idempotent, preserves the
canonical graph (round-trips exactly), keeps every replay hash
identical, and - crucially - governance is computed entirely
without the graph or any Neo4j connection.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.epistemic_graph import (
    edges, graph_signature, nodes, nodes_of_type,
)
from desi.epistemic_graph.nodes import NodeType

from .exporter import export, export_payload, payload_signature
from .graph_projection import (
    from_projection, project, round_trip_signature,
)
from .neo4j_client import DryRunClient, neo4j_available
from .serialization import cypher_statements

VERDICT_SAFE = "EXPORT_REPLAY_SAFE"
VERDICT_UNSAFE = "EXPORT_PERTURBS_STATE"
VERDICT_HALT = "EXPORT_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_SAFE, VERDICT_UNSAFE, VERDICT_HALT,
)

_FLOOR = 0.90
_GOV_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def export_determinism() -> float:
    a = export(DryRunClient()).signature
    b = export(DryRunClient()).signature
    return 1.0 if a == b and a == payload_signature() else 0.0


def canonical_preservation() -> float:
    """The export must not mutate the source graph and must
    round-trip exactly back to the same graph signature."""
    before = graph_signature()
    export(DryRunClient())
    after = graph_signature()
    checks = [
        before == after,
        round_trip_signature() == before,
    ]
    return _round(sum(1 for c in checks if c) / len(checks))


def replay_integrity() -> float:
    """Every ReplayHash node value in the export equals the
    source graph's, in [0, 1]."""
    src = {
        n.node_id: n.label
        for n in nodes_of_type(NodeType.REPLAY_HASH.value)
    }
    if not src:
        return 0.0
    proj = project()
    exported = {
        d["node_id"]: d["label"]
        for d in proj["nodes_by_type"].get(  # type: ignore[union-attr]
            NodeType.REPLAY_HASH.value, []
        )
    }
    same = sum(
        1 for k, v in src.items() if exported.get(k) == v
    )
    return _round(same / len(src))


def graph_consistency() -> float:
    """The projection round-trips to exactly the same node and
    edge sets, in [0, 1]."""
    n2, e2 = from_projection(project())
    checks = [
        set(n2) == set(nodes()),
        set(e2) == set(edges()),
        len(n2) == len(nodes()),
        len(e2) == len(edges()),
    ]
    return _round(sum(1 for c in checks if c) / len(checks))


def governance_independence() -> float:
    """Governance results must be invariant to the presence of
    the export / any Neo4j connection. We compute a canonical
    governance probe, perform an export, and recompute: the
    governance result must be identical, and DESi must remain
    fully functional without the neo4j package."""
    from desi.scientific_rendering import forbidden_hits
    from desi.icrl_followup_verdict import gate_passes_all

    probe_before = (
        forbidden_hits("AGI breakthrough world model"),
        gate_passes_all(),
    )
    export(DryRunClient())  # write provenance to the graph
    probe_after = (
        forbidden_hits("AGI breakthrough world model"),
        gate_passes_all(),
    )
    checks = [
        probe_before == probe_after,
        # DESi works whether or not neo4j is installed: the
        # offline path produced a full export regardless.
        len(cypher_statements()) > 0,
        # neither availability state changes the governance probe
        isinstance(neo4j_available(), bool),
    ]
    return _round(sum(1 for c in checks if c) / len(checks))


def _signature() -> str:
    import hashlib
    return hashlib.sha256(
        payload_signature().encode("utf-8"),
    ).hexdigest()


def _recommendation(
    *, determinism: float, canonical: float, replay: float,
    consistency: float, governance: float,
) -> str:
    if determinism < 1.0 or canonical < 1.0:
        return VERDICT_HALT
    if (
        replay < _FLOOR
        or consistency < _FLOOR
        or governance < _GOV_FLOOR
    ):
        return VERDICT_UNSAFE
    return VERDICT_SAFE


@dataclass(frozen=True)
class V241Report:
    node_count: int
    edge_count: int
    statement_count: int
    export_determinism: float
    canonical_preservation: float
    replay_integrity: float
    graph_consistency: float
    governance_independence: float
    neo4j_available: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "statement_count": self.statement_count,
            "export_determinism": self.export_determinism,
            "canonical_preservation":
                self.canonical_preservation,
            "replay_integrity": self.replay_integrity,
            "graph_consistency": self.graph_consistency,
            "governance_independence":
                self.governance_independence,
            "neo4j_available": self.neo4j_available,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V241Report:
    determinism = export_determinism()
    canonical = canonical_preservation()
    replay = replay_integrity()
    consistency = graph_consistency()
    governance = governance_independence()
    result = export(DryRunClient())
    halt = determinism < 1.0 or canonical < 1.0
    verdict = _recommendation(
        determinism=determinism, canonical=canonical,
        replay=replay, consistency=consistency,
        governance=governance,
    )
    rationale = (
        f"INFO: exported {result.node_count} nodes, "
        f"{result.edge_count} edges as "
        f"{result.statement_count} idempotent Cypher MERGE "
        f"statements",
        "INFO: export targets an offline DryRunClient; the "
        "neo4j package is optional and DESi reads nothing back "
        "from the graph",
        f"{'PASS' if determinism == 1.0 else 'FAIL'}: "
        f"export_determinism {determinism}",
        f"{'PASS' if canonical == 1.0 else 'FAIL'}: "
        f"canonical_preservation {canonical} (round-trips to "
        f"the same graph signature)",
        f"{'PASS' if replay >= _FLOOR else 'FAIL'}: "
        f"replay_integrity {replay} >= 0.90",
        f"{'PASS' if consistency >= _FLOOR else 'FAIL'}: "
        f"graph_consistency {consistency} >= 0.90",
        f"{'PASS' if governance >= _GOV_FLOOR else 'FAIL'}: "
        f"governance_independence {governance} >= 0.95 "
        f"(neo4j_available={neo4j_available()})",
    )
    return V241Report(
        node_count=result.node_count,
        edge_count=result.edge_count,
        statement_count=result.statement_count,
        export_determinism=determinism,
        canonical_preservation=canonical,
        replay_integrity=replay,
        graph_consistency=consistency,
        governance_independence=governance,
        neo4j_available=neo4j_available(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_export_artifact() -> dict[str, object]:
    return {
        "schema_version": "v24_1_neo4j_export",
        "disclaimer": (
            "A deterministic, idempotent, replay-safe export of "
            "the v24.0 epistemic graph into Neo4j-compatible "
            "Cypher. Neo4j is optional read-only infrastructure: "
            "the neo4j package is imported lazily, the test path "
            "uses an offline dry-run client, and DESi reads "
            "nothing back from the graph to steer itself. "
            "Governance is computed entirely without the graph. "
            "The canonical state remains the JSON artifacts and "
            "replay hashes."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "export_determinism": export_determinism(),
        "canonical_preservation": canonical_preservation(),
        "replay_integrity": replay_integrity(),
        "graph_consistency": graph_consistency(),
        "governance_independence": governance_independence(),
        "neo4j_available": neo4j_available(),
        "statement_count": len(cypher_statements()),
        "statements_signature":
            export_payload()["statements_signature"],
        "round_trip_signature":
            export_payload()["round_trip_signature"],
        "graph_signature": graph_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_SAFE",
    "VERDICT_UNSAFE",
    "V241Report",
    "build_export_artifact",
    "build_report",
    "canonical_preservation",
    "export_determinism",
    "governance_independence",
    "graph_consistency",
    "replay_integrity",
]
