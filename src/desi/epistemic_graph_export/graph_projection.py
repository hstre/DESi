"""v24.1 - graph projection and round-trip.

Projects the v24.0 graph into a label-grouped structure for
export, and reconstructs nodes/edges from that projection. The
round-trip is the canonical-preservation check: re-importing the
projection must reproduce the exact same graph signature.
"""
from __future__ import annotations

from desi.epistemic_graph import edges, nodes
from desi.epistemic_graph.edges import Edge
from desi.epistemic_graph.lineage import _signature_of
from desi.epistemic_graph.nodes import Node


def project() -> dict[str, object]:
    nodes_by_type: dict[str, list[dict[str, object]]] = {}
    for n in nodes():
        nodes_by_type.setdefault(n.node_type, []).append(
            n.to_dict(),
        )
    edges_by_type: dict[str, list[dict[str, object]]] = {}
    for e in edges():
        edges_by_type.setdefault(e.edge_type, []).append(
            e.to_dict(),
        )
    return {
        "nodes_by_type": {
            k: nodes_by_type[k] for k in sorted(nodes_by_type)
        },
        "edges_by_type": {
            k: edges_by_type[k] for k in sorted(edges_by_type)
        },
    }


def from_projection(
    proj: dict[str, object],
) -> tuple[tuple[Node, ...], tuple[Edge, ...]]:
    nbt: dict = proj["nodes_by_type"]  # type: ignore[assignment]
    ebt: dict = proj["edges_by_type"]  # type: ignore[assignment]
    rebuilt_nodes = [
        Node(d["node_id"], d["node_type"], d["label"])
        for group in nbt.values()
        for d in group
    ]
    rebuilt_edges = [
        Edge(d["source"], d["target"], d["edge_type"])
        for group in ebt.values()
        for d in group
    ]
    node_tuple = tuple(
        sorted(rebuilt_nodes, key=lambda n: n.sort_key())
    )
    edge_tuple = tuple(
        sorted(rebuilt_edges, key=lambda e: e.sort_key())
    )
    return node_tuple, edge_tuple


def round_trip_signature() -> str:
    return _signature_of(from_projection(project()))


def projection_signature() -> str:
    return _signature_of((nodes(), edges()))


__all__ = [
    "from_projection",
    "project",
    "projection_signature",
    "round_trip_signature",
]
