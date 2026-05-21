"""v30.0 - Mutation Memory Topology report.

Pflichtmetriken (directive § v30.0):

* lineage_visibility
* decision_visibility
* rejection_visibility
* evolution_traceability
* replay_stability

Killerfrage: "Kann DESi evolutionaere Entscheidungen dauerhaft
epistemisch strukturieren?"

Every mutation idea - accepted or rejected - is preserved as an
epistemic event with its proposer, target, provenance, decision,
reason and consequence. Read-only history; nothing is learned
implicitly, nothing is deleted.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .decisions import decisions
from .lineage import (
    edges, edges_of_type, graph_signature, mutation_edge_kinds,
    nodes,
)
from .memory_schema import (
    EDGE_TYPES, NODE_TYPES, is_valid_triple,
)
from .mutations import (
    accepted_mutations, mutations, rejected_mutations,
)

VERDICT_STRUCTURED = "EVOLUTION_MEMORY_STRUCTURED"
VERDICT_PARTIAL = "EVOLUTION_MEMORY_INCOMPLETE"
VERDICT_HALT = "MEMORY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def invalid_edges() -> tuple[tuple[str, str, str], ...]:
    types = {n.node_id: n.node_type for n in nodes()}
    bad: list[tuple[str, str, str]] = []
    for e in edges():
        st, tt = types.get(e.source), types.get(e.target)
        if st is None or tt is None or not is_valid_triple(
            st, e.edge_type, tt,
        ):
            bad.append((e.source, e.edge_type, e.target))
    return tuple(sorted(bad))


def lineage_visibility() -> float:
    ms = mutations()
    if not ms:
        return 0.0
    visible = sum(
        1 for m in ms
        if {"PROPOSED_BY", "TARGETS"}.issubset(
            mutation_edge_kinds(m.mutation_id))
    )
    return _round(visible / len(ms))


def decision_visibility() -> float:
    ms = mutations()
    if not ms:
        return 0.0
    decided = {d.mutation_id for d in decisions()}
    seen = sum(1 for m in ms if m.mutation_id in decided)
    return _round(seen / len(ms))


def rejection_visibility() -> float:
    rejected = rejected_mutations()
    if not rejected:
        return 1.0
    visible = sum(
        1 for m in rejected
        if {"REJECTED_BECAUSE", "INVALIDATED_BY"}.issubset(
            mutation_edge_kinds(m.mutation_id))
    )
    return _round(visible / len(rejected))


def evolution_traceability() -> float:
    ms = mutations()
    if not ms:
        return 0.0
    decided = {d.mutation_id for d in decisions()}
    ok = 0
    for m in ms:
        kinds = mutation_edge_kinds(m.mutation_id)
        base = (
            {"PROPOSED_BY", "TARGETS", "EVALUATED_BY"}.issubset(kinds)
            and m.mutation_id in decided
        )
        consequence = (
            "ACCEPTED_BECAUSE" in kinds if m.accepted
            else {"REJECTED_BECAUSE", "INVALIDATED_BY"}.issubset(kinds)
        )
        if base and consequence:
            ok += 1
    return _round(ok / len(ms))


def replay_stability() -> float:
    if graph_signature() != graph_signature():
        return 0.0
    return 1.0 if not invalid_edges() else 0.0


def _recommendation(
    *, replay: float, lineage: float, decision: float,
    rejection: float, traceability: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        lineage < _FLOOR
        or decision < _FLOOR
        or rejection < _FLOOR
        or traceability < _FLOOR
    ):
        return VERDICT_PARTIAL
    return VERDICT_STRUCTURED


@dataclass(frozen=True)
class V300Report:
    node_count: int
    edge_count: int
    mutation_count: int
    accepted_count: int
    rejected_count: int
    lineage_visibility: float
    decision_visibility: float
    rejection_visibility: float
    evolution_traceability: float
    replay_stability: float
    invalid_edges: tuple[tuple[str, str, str], ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "mutation_count": self.mutation_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "lineage_visibility": self.lineage_visibility,
            "decision_visibility": self.decision_visibility,
            "rejection_visibility": self.rejection_visibility,
            "evolution_traceability": self.evolution_traceability,
            "replay_stability": self.replay_stability,
            "invalid_edges": [list(t) for t in self.invalid_edges],
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V300Report:
    lineage = lineage_visibility()
    decision = decision_visibility()
    rejection = rejection_visibility()
    traceability = evolution_traceability()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, lineage=lineage, decision=decision,
        rejection=rejection, traceability=traceability,
    )
    rationale = (
        f"INFO: {len(mutations())} mutation ideas "
        f"({len(accepted_mutations())} accepted, "
        f"{len(rejected_mutations())} rejected and kept); "
        f"{len(nodes())} nodes, {len(edges())} edges",
        "INFO: read-only evolution history; nothing learned "
        "implicitly, no policy adaptation, nothing deleted",
        f"{'PASS' if lineage >= _FLOOR else 'FAIL'}: "
        f"lineage_visibility {lineage} >= 0.95",
        f"{'PASS' if decision >= _FLOOR else 'FAIL'}: "
        f"decision_visibility {decision} >= 0.95",
        f"{'PASS' if rejection >= _FLOOR else 'FAIL'}: "
        f"rejection_visibility {rejection} >= 0.95 (rejected "
        f"ideas preserved with reasons)",
        f"{'PASS' if traceability >= _FLOOR else 'FAIL'}: "
        f"evolution_traceability {traceability} >= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (invalid_edges "
        f"{[list(t) for t in invalid_edges()]}; signature "
        f"{graph_signature()[:12]})",
    )
    return V300Report(
        node_count=len(nodes()),
        edge_count=len(edges()),
        mutation_count=len(mutations()),
        accepted_count=len(accepted_mutations()),
        rejected_count=len(rejected_mutations()),
        lineage_visibility=lineage,
        decision_visibility=decision,
        rejection_visibility=rejection,
        evolution_traceability=traceability,
        replay_stability=replay,
        invalid_edges=invalid_edges(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_topology_artifact() -> dict[str, object]:
    return {
        "schema_version": "v30_0_mutation_memory_topology",
        "disclaimer": (
            "A read-only epistemic evolution-memory graph. Every "
            "mutation idea DESi has produced - accepted or "
            "rejected - is preserved as an epistemic event with "
            "its proposer, target, provenance, decision, reason "
            "and consequence. Rejected ideas are never deleted. "
            "This is history, not a learning layer: no implicit "
            "learning, no automatic policy adaptation, no hidden "
            "optimisation memory, no governance change. "
            "Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "node_types": list(NODE_TYPES),
        "edge_types": list(EDGE_TYPES),
        "mutations": [m.to_dict() for m in mutations()],
        "decisions": [d.to_dict() for d in decisions()],
        "nodes": [n.to_dict() for n in nodes()],
        "edges": [e.to_dict() for e in edges()],
        "lineage_visibility": lineage_visibility(),
        "decision_visibility": decision_visibility(),
        "rejection_visibility": rejection_visibility(),
        "evolution_traceability": evolution_traceability(),
        "replay_stability": replay_stability(),
        "invalid_edges": [list(t) for t in invalid_edges()],
        "graph_signature": graph_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_STRUCTURED",
    "V300Report",
    "build_report",
    "build_topology_artifact",
    "decision_visibility",
    "evolution_traceability",
    "invalid_edges",
    "lineage_visibility",
    "rejection_visibility",
    "replay_stability",
]
