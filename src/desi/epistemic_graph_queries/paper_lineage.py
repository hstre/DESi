"""v24.3 - automatic paper lineage and condition reconstruction.

Builds the lineage from each paper artifact down to the claims,
sprints, fixtures and limitations it rests on, and reconstructs
the experimental conditions of each claim straight from the
graph. Also checks the provenance graph is a clean DAG with no
dangling references.
"""
from __future__ import annotations

from desi.epistemic_graph import edges, edges_of_type, nodes, nodes_of_type
from desi.epistemic_graph.nodes import NodeType

from .queries import (
    claim_ids, fixtures_of, generating_sprints, limitations_of,
)


def _strip(node_id: str) -> str:
    return node_id.split(":", 1)[1]


def artifact_ids() -> tuple[str, ...]:
    return tuple(
        _strip(n.node_id)
        for n in nodes_of_type(NodeType.ARTIFACT.value)
    )


def _artifact_sprint(artifact_id: str) -> str | None:
    for e in edges_of_type("GENERATED_IN"):
        if e.source == f"artifact:{artifact_id}":
            return _strip(e.target)
    return None


def claims_in_sprint(sprint: str) -> tuple[str, ...]:
    return tuple(sorted(
        _strip(e.source) for e in edges_of_type("GENERATED_IN")
        if e.source.startswith("claim:")
        and e.target == f"sprint:{sprint}"
    ))


def paper_lineage() -> tuple[dict[str, object], ...]:
    out: list[dict[str, object]] = []
    for aid in artifact_ids():
        sprint = _artifact_sprint(aid)
        out.append({
            "artifact": aid,
            "sprint": sprint,
            "claims": list(
                claims_in_sprint(sprint) if sprint else ()
            ),
        })
    return tuple(out)


def condition_reconstruction() -> float:
    """Fraction of claims whose experimental conditions (fixture,
    sprint and scope/limitation) are reconstructible from the
    graph, in [0, 1]."""
    ids = claim_ids()
    if not ids:
        return 0.0
    ok = sum(
        1 for c in ids
        if fixtures_of(c) and generating_sprints(c)
        and limitations_of(c)
    )
    return round(ok / len(ids), 6)


def _adjacency() -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {}
    for e in edges():
        adj.setdefault(e.source, []).append(e.target)
    return adj


def has_dangling_edges() -> bool:
    ids = {n.node_id for n in nodes()}
    return any(
        e.source not in ids or e.target not in ids
        for e in edges()
    )


def has_cycle() -> bool:
    adj = _adjacency()
    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def visit(node: str) -> bool:
        color[node] = GREY
        for nxt in adj.get(node, ()):  # neighbours
            c = color.get(nxt, WHITE)
            if c == GREY:
                return True
            if c == WHITE and visit(nxt):
                return True
        color[node] = BLACK
        return False

    for n in {x.node_id for x in nodes()}:
        if color.get(n, WHITE) == WHITE:
            if visit(n):
                return True
    return False


def lineage_integrity() -> float:
    """1.0 iff the provenance graph has no dangling edges and is
    acyclic (a clean DAG)."""
    checks = [not has_dangling_edges(), not has_cycle()]
    return round(sum(1 for c in checks if c) / len(checks), 6)


__all__ = [
    "artifact_ids",
    "claims_in_sprint",
    "condition_reconstruction",
    "has_cycle",
    "has_dangling_edges",
    "lineage_integrity",
    "paper_lineage",
]
