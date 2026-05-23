"""v27.1 - Claim Graph & Neo4j Integration report.

Pflichtmetriken (directive § v27.1):

* graph_connectivity
* conflict_visibility
* open_problem_visibility
* lineage_integrity
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Forschung als
expliziten epistemischen Graphen darstellen?"

Research is rendered as a read-only claim graph: interweavings,
conflicts and open research spaces are made visible. Neo4j stays
optional read-only infrastructure; nothing is ranked.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.research_harvester import papers
from desi.research_harvester.taxonomy import ClaimClass as K

from .graph_builder import (
    determinism_signatures, edges, edges_of_type,
    graph_signature, nodes, nodes_of_type,
)
from .lineage import (
    connected_node_fraction, has_cycle, has_dangling_edges,
    invalid_edges,
)
from .neo4j_projection import (
    cypher_statements, neo4j_available, project,
    statements_signature,
)
from .relations import EDGE_TYPES, NODE_TYPES, NodeType

VERDICT_GRAPHED = "RESEARCH_AS_EXPLICIT_GRAPH"
VERDICT_PARTIAL = "GRAPH_INCOMPLETE"
VERDICT_HALT = "GRAPH_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_GRAPHED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def graph_connectivity() -> float:
    return connected_node_fraction()


def conflict_visibility() -> float:
    """Fraction of declared cross-paper conflicts represented as
    CONFLICTS_WITH edges, in [0, 1]."""
    declared = sum(len(p.conflicts) for p in papers())
    if declared == 0:
        return 1.0
    represented = len(edges_of_type("CONFLICTS_WITH"))
    return _round(min(represented, declared) / declared)


def open_problem_visibility() -> float:
    """Fraction of open-question claims represented as
    OpenQuestion nodes with a LEAVES_OPEN edge, in [0, 1]."""
    open_claims = sum(
        1 for p in papers() for c in p.claims
        if c.claim_class == K.OPEN_QUESTION.value
    )
    if open_claims == 0:
        return 1.0
    oq_nodes = len(nodes_of_type(NodeType.OPEN_QUESTION.value))
    leaves = len(edges_of_type("LEAVES_OPEN"))
    return _round(min(oq_nodes, leaves, open_claims) / open_claims)


def lineage_integrity() -> float:
    """1.0 iff there are no invalid edges, no dangling edges and
    the graph is acyclic."""
    checks = [
        not invalid_edges(),
        not has_dangling_edges(),
        not has_cycle(),
    ]
    return _round(sum(1 for c in checks if c) / len(checks))


def replay_stability() -> float:
    a, b = determinism_signatures()
    if a != b:
        return 0.0
    if graph_signature() != graph_signature():
        return 0.0
    return 1.0 if statements_signature() == statements_signature() else 0.0


def _recommendation(
    *, replay: float, connectivity: float, conflict: float,
    open_p: float, integrity: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        connectivity < _FLOOR
        or conflict < _FLOOR
        or open_p < _FLOOR
        or integrity < 0.95
    ):
        return VERDICT_PARTIAL
    return VERDICT_GRAPHED


@dataclass(frozen=True)
class V271Report:
    node_count: int
    edge_count: int
    node_type_count: int
    edge_type_count: int
    graph_connectivity: float
    conflict_visibility: float
    open_problem_visibility: float
    lineage_integrity: float
    replay_stability: float
    invalid_edges: tuple[tuple[str, str, str], ...]
    neo4j_available: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "node_type_count": self.node_type_count,
            "edge_type_count": self.edge_type_count,
            "graph_connectivity": self.graph_connectivity,
            "conflict_visibility": self.conflict_visibility,
            "open_problem_visibility":
                self.open_problem_visibility,
            "lineage_integrity": self.lineage_integrity,
            "replay_stability": self.replay_stability,
            "invalid_edges": [list(t) for t in self.invalid_edges],
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


def build_report() -> V271Report:
    connectivity = graph_connectivity()
    conflict = conflict_visibility()
    open_p = open_problem_visibility()
    integrity = lineage_integrity()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, connectivity=connectivity,
        conflict=conflict, open_p=open_p, integrity=integrity,
    )
    rationale = (
        f"INFO: {len(nodes())} nodes across "
        f"{len({n.node_type for n in nodes()})} types; "
        f"{len(edges())} edges across "
        f"{len({e.edge_type for e in edges()})} types",
        "INFO: read-only claim graph over the corpus; conflicts "
        "are made visible, never adjudicated; nothing is ranked",
        f"{'PASS' if connectivity >= _FLOOR else 'FAIL'}: "
        f"graph_connectivity {connectivity} >= 0.90",
        f"{'PASS' if conflict >= _FLOOR else 'FAIL'}: "
        f"conflict_visibility {conflict} >= 0.90 "
        f"({len(edges_of_type('CONFLICTS_WITH'))} conflict "
        f"edges)",
        f"{'PASS' if open_p >= _FLOOR else 'FAIL'}: "
        f"open_problem_visibility {open_p} >= 0.90",
        f"{'PASS' if integrity >= 0.95 else 'FAIL'}: "
        f"lineage_integrity {integrity} (invalid "
        f"{[list(t) for t in invalid_edges()]}; dangling "
        f"{has_dangling_edges()}; cycle {has_cycle()})",
        f"INFO: neo4j optional (available={neo4j_available()}); "
        f"{len(cypher_statements())} Cypher statements via "
        f"offline DryRunClient",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{graph_signature()[:12]})",
    )
    return V271Report(
        node_count=len(nodes()),
        edge_count=len(edges()),
        node_type_count=len({n.node_type for n in nodes()}),
        edge_type_count=len({e.edge_type for e in edges()}),
        graph_connectivity=connectivity,
        conflict_visibility=conflict,
        open_problem_visibility=open_p,
        lineage_integrity=integrity,
        replay_stability=replay,
        invalid_edges=invalid_edges(),
        neo4j_available=neo4j_available(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_graph_artifact() -> dict[str, object]:
    return {
        "schema_version": "v27_1_claim_graph",
        "disclaimer": (
            "A read-only research claim graph built from the "
            "v27.0 corpus. Papers, claims, methods, metrics, "
            "datasets, authors, limitations and open questions "
            "are nodes; their CLAIMS / SUPPORTS / CONFLICTS_WITH "
            "/ EXTENDS / REUSES_* / LEAVES_OPEN / LIMITED_BY / "
            "DERIVED_FROM relations are edges. Neo4j is optional "
            "read-only infrastructure (offline dry-run in tests, "
            "lazy driver import); DESi reads nothing back and "
            "ranks nothing. Conflicts are made visible, never "
            "adjudicated. Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "node_types": list(NODE_TYPES),
        "edge_types": list(EDGE_TYPES),
        "nodes": [n.to_dict() for n in nodes()],
        "edges": [e.to_dict() for e in edges()],
        "graph_connectivity": graph_connectivity(),
        "conflict_visibility": conflict_visibility(),
        "open_problem_visibility": open_problem_visibility(),
        "lineage_integrity": lineage_integrity(),
        "replay_stability": replay_stability(),
        "invalid_edges": [list(t) for t in invalid_edges()],
        "neo4j_available": neo4j_available(),
        "statement_count": len(cypher_statements()),
        "statements_signature": statements_signature(),
        "graph_signature": graph_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_GRAPHED",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "V271Report",
    "build_graph_artifact",
    "build_report",
    "conflict_visibility",
    "graph_connectivity",
    "lineage_integrity",
    "open_problem_visibility",
    "replay_stability",
]
