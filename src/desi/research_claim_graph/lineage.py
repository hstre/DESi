"""v27.1 - claim-graph lineage and integrity.

Provenance queries over the claim graph plus an integrity check
that the graph is a clean DAG with no dangling edges and only
schema-valid triples.
"""
from __future__ import annotations

from .graph_builder import edges, nodes
from .relations import is_valid_triple


def _node_types() -> dict[str, str]:
    return {n.node_id: n.node_type for n in nodes()}


def out_edges(node_id: str) -> tuple:
    return tuple(e for e in edges() if e.source == node_id)


def invalid_edges() -> tuple[tuple[str, str, str], ...]:
    types = _node_types()
    bad: list[tuple[str, str, str]] = []
    for e in edges():
        st = types.get(e.source)
        tt = types.get(e.target)
        if st is None or tt is None or not is_valid_triple(
            st, e.edge_type, tt,
        ):
            bad.append((e.source, e.edge_type, e.target))
    return tuple(sorted(bad))


def has_dangling_edges() -> bool:
    ids = {n.node_id for n in nodes()}
    return any(
        e.source not in ids or e.target not in ids
        for e in edges()
    )


def _adjacency() -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {}
    for e in edges():
        adj.setdefault(e.source, []).append(e.target)
    return adj


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


def connected_node_fraction() -> float:
    if not nodes():
        return 0.0
    incident: set[str] = set()
    for e in edges():
        incident.add(e.source)
        incident.add(e.target)
    return round(
        len(incident & {n.node_id for n in nodes()})
        / len(nodes()), 6,
    )


__all__ = [
    "connected_node_fraction",
    "has_cycle",
    "has_dangling_edges",
    "invalid_edges",
    "out_edges",
]
