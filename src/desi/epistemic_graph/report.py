"""v24.0 - Epistemic Graph Schema report.

Pflichtmetriken (directive § v24.0):

* schema_coverage
* lineage_visibility
* conflict_visibility
* graph_determinism
* replay_stability

Killerfrage: "Kann DESi epistemische Zustaende explizit
darstellen statt nur Resultate zu speichern?"

The graph is read-only epistemic structure over the canonical
JSON artifacts: it models claims, provenance, conflicts and
replay hashes without recomputing or ranking anything.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.icrl_followup_revision import claims

from .edges import EDGE_TYPES
from .lineage import (
    claim_lineage_visible, determinism_signatures, edges,
    edges_of_type, graph_signature, nodes, nodes_of_type,
)
from .nodes import NODE_TYPES, NodeType
from .schema import (
    is_valid_triple, required_edge_types, required_node_types,
    schema_signature,
)

VERDICT_EXPLICIT = "EPISTEMIC_STATE_EXPLICIT"
VERDICT_OPAQUE = "STATE_STILL_OPAQUE"
VERDICT_HALT = "GRAPH_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_EXPLICIT, VERDICT_OPAQUE, VERDICT_HALT,
)

_COVERAGE_FLOOR = 0.90
_LINEAGE_FLOOR = 0.90
_CONFLICT_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _node_type_of() -> dict[str, str]:
    return {n.node_id: n.node_type for n in nodes()}


def invalid_edges() -> tuple[tuple[str, str, str], ...]:
    """Edges whose (source_type, edge_type, target_type) is not
    an allowed schema triple - must be empty."""
    types = _node_type_of()
    bad: list[tuple[str, str, str]] = []
    for e in edges():
        st = types.get(e.source)
        tt = types.get(e.target)
        if st is None or tt is None:
            bad.append((e.source, e.edge_type, e.target))
        elif not is_valid_triple(st, e.edge_type, tt):
            bad.append((e.source, e.edge_type, e.target))
    return tuple(sorted(bad))


def present_node_types() -> frozenset[str]:
    return frozenset(n.node_type for n in nodes())


def present_edge_types() -> frozenset[str]:
    return frozenset(e.edge_type for e in edges())


def schema_coverage() -> float:
    """Fraction of the required node and edge types that have
    at least one instance in the graph, in [0, 1]."""
    req_n = set(required_node_types())
    req_e = set(required_edge_types())
    have_n = present_node_types() & req_n
    have_e = present_edge_types() & req_e
    return _round(
        (len(have_n) + len(have_e)) / (len(req_n) + len(req_e))
    )


def lineage_visibility() -> float:
    """Fraction of claim nodes with a fully visible lineage
    chain, in [0, 1]."""
    claim_nodes = nodes_of_type(NodeType.CLAIM.value)
    if not claim_nodes:
        return 0.0
    visible = sum(
        1 for c in claim_nodes
        if claim_lineage_visible(c.node_id.split(":", 1)[1])
    )
    return _round(visible / len(claim_nodes))


def conflict_visibility() -> float:
    """Fraction of dissent-path nodes referenced by at least
    one CONFLICTS_WITH edge, in [0, 1]."""
    dissent = nodes_of_type(NodeType.DISSENT_PATH.value)
    if not dissent:
        return 1.0
    referenced = {
        e.target for e in edges_of_type("CONFLICTS_WITH")
    }
    seen = sum(1 for d in dissent if d.node_id in referenced)
    return _round(seen / len(dissent))


def graph_determinism() -> float:
    """1.0 iff two independent from-scratch builds produce the
    identical graph signature."""
    a, b = determinism_signatures()
    return 1.0 if a == b else 0.0


def replay_stability() -> float:
    """1.0 iff the graph signature is stable and the schema
    signature is stable across recomputation."""
    if graph_signature() != graph_signature():
        return 0.0
    if schema_signature() != schema_signature():
        return 0.0
    return 1.0 if graph_determinism() == 1.0 else 0.0


def _recommendation(
    *, replay: float, coverage: float, lineage: float,
    conflict: float, determinism: float, clean: bool,
) -> str:
    if replay < 1.0 or determinism < 1.0:
        return VERDICT_HALT
    if (
        not clean
        or coverage < _COVERAGE_FLOOR
        or lineage < _LINEAGE_FLOOR
        or conflict < _CONFLICT_FLOOR
    ):
        return VERDICT_OPAQUE
    return VERDICT_EXPLICIT


@dataclass(frozen=True)
class V240Report:
    node_count: int
    edge_count: int
    node_type_count: int
    edge_type_count: int
    schema_coverage: float
    lineage_visibility: float
    conflict_visibility: float
    graph_determinism: float
    replay_stability: float
    invalid_edges: tuple[tuple[str, str, str], ...]
    missing_node_types: tuple[str, ...]
    missing_edge_types: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "node_type_count": self.node_type_count,
            "edge_type_count": self.edge_type_count,
            "schema_coverage": self.schema_coverage,
            "lineage_visibility": self.lineage_visibility,
            "conflict_visibility": self.conflict_visibility,
            "graph_determinism": self.graph_determinism,
            "replay_stability": self.replay_stability,
            "invalid_edges": [list(t) for t in self.invalid_edges],
            "missing_node_types": list(self.missing_node_types),
            "missing_edge_types": list(self.missing_edge_types),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _missing_node_types() -> tuple[str, ...]:
    return tuple(sorted(
        set(required_node_types()) - present_node_types()
    ))


def _missing_edge_types() -> tuple[str, ...]:
    return tuple(sorted(
        set(required_edge_types()) - present_edge_types()
    ))


def build_report() -> V240Report:
    coverage = schema_coverage()
    lineage = lineage_visibility()
    conflict = conflict_visibility()
    determinism = graph_determinism()
    replay = replay_stability()
    bad = invalid_edges()
    clean = not bad
    halt = replay < 1.0 or determinism < 1.0
    verdict = _recommendation(
        replay=replay, coverage=coverage, lineage=lineage,
        conflict=conflict, determinism=determinism, clean=clean,
    )
    rationale = (
        f"INFO: {len(nodes())} nodes across "
        f"{len(present_node_types())} types; {len(edges())} "
        f"edges across {len(present_edge_types())} types",
        "INFO: read-only structure over canonical JSON; node "
        "values are not recomputed and the graph ranks nothing",
        f"{'PASS' if coverage >= 0.90 else 'FAIL'}: "
        f"schema_coverage {coverage} >= 0.90 (missing nodes "
        f"{list(_missing_node_types())}; missing edges "
        f"{list(_missing_edge_types())})",
        f"{'PASS' if lineage >= 0.90 else 'FAIL'}: "
        f"lineage_visibility {lineage} >= 0.90",
        f"{'PASS' if conflict >= 0.90 else 'FAIL'}: "
        f"conflict_visibility {conflict} >= 0.90",
        f"{'PASS' if clean else 'FAIL'}: invalid_edges "
        f"{[list(t) for t in bad]} (must be empty)",
        f"{'PASS' if determinism == 1.0 else 'FAIL'}: "
        f"graph_determinism {determinism}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{graph_signature()[:12]})",
    )
    return V240Report(
        node_count=len(nodes()),
        edge_count=len(edges()),
        node_type_count=len(present_node_types()),
        edge_type_count=len(present_edge_types()),
        schema_coverage=coverage,
        lineage_visibility=lineage,
        conflict_visibility=conflict,
        graph_determinism=determinism,
        replay_stability=replay,
        invalid_edges=bad,
        missing_node_types=_missing_node_types(),
        missing_edge_types=_missing_edge_types(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_schema_artifact() -> dict[str, object]:
    return {
        "schema_version": "v24_0_epistemic_graph_schema",
        "disclaimer": (
            "A read-only epistemic graph layered over the "
            "canonical JSON artifacts. It models claims, "
            "provenance, conflicts, governance rules and replay "
            "hashes as explicit nodes and edges. It stores why "
            "results are valid, not the results themselves; it "
            "makes no decision, ranks nothing, and changes no "
            "replay. The canonical state remains the JSON "
            "artifacts and replay hashes. Deterministic."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "node_types": list(NODE_TYPES),
        "edge_types": list(EDGE_TYPES),
        "nodes": [n.to_dict() for n in nodes()],
        "edges": [e.to_dict() for e in edges()],
        "schema_coverage": schema_coverage(),
        "lineage_visibility": lineage_visibility(),
        "conflict_visibility": conflict_visibility(),
        "graph_determinism": graph_determinism(),
        "replay_stability": replay_stability(),
        "invalid_edges": [list(t) for t in invalid_edges()],
        "graph_signature": graph_signature(),
        "schema_signature": schema_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_EXPLICIT",
    "VERDICT_HALT",
    "VERDICT_OPAQUE",
    "V240Report",
    "build_report",
    "build_schema_artifact",
    "conflict_visibility",
    "graph_determinism",
    "invalid_edges",
    "lineage_visibility",
    "replay_stability",
    "schema_coverage",
]
