"""v27.1 - deterministic claim-graph construction.

Builds the read-only research claim graph from the v27.0 corpus:
papers, claims, methods, metrics, datasets, authors, limitations
and open questions as nodes, and their CLAIMS / SUPPORTS /
CONFLICTS_WITH / EXTENDS / REUSES_* / LEAVES_OPEN / LIMITED_BY /
DERIVED_FROM relations as edges. Pure and deterministic.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache

from desi.research_harvester import papers
from desi.research_harvester.taxonomy import ClaimClass as K

from .relations import Edge, Node, NodeType

_PRIMARY_CLASSES = (
    K.EXPERIMENTAL.value, K.THEORETICAL.value, K.EMPIRICAL.value,
)
_SUPPORT_CLASSES = (
    K.COMPARATIVE.value, K.REPRODUCIBILITY.value,
    K.EMPIRICAL.value,
)


def _primary_claim_id(paper) -> str | None:
    for c in paper.claims:
        if c.claim_class in _PRIMARY_CLASSES:
            return c.claim_id
    return None


def _construct() -> tuple[tuple[Node, ...], tuple[Edge, ...]]:
    nodes: dict[str, Node] = {}
    edges: set[Edge] = set()

    def add_node(nid: str, ntype: NodeType, label: str) -> str:
        if nid not in nodes:
            nodes[nid] = Node(nid, ntype.value, label)
        return nid

    def add_edge(src: str, dst: str, etype) -> None:
        edges.add(Edge(src, dst, etype.value))

    from .relations import EdgeType as E

    for p in papers():
        pid = f"paper:{p.paper_id}"
        add_node(pid, NodeType.PAPER, p.metadata.title)
        primary = _primary_claim_id(p)
        for c in p.claims:
            cid = f"claim:{c.claim_id}"
            add_node(cid, NodeType.CLAIM, c.text)
            add_edge(pid, cid, E.CLAIMS)
            for author in p.metadata.authors:
                aid = f"author:{author}"
                add_node(aid, NodeType.AUTHOR, author)
                add_edge(aid, cid, E.CLAIMS)
            if c.is_limitation():
                lid = f"limitation:{c.claim_id}"
                add_node(lid, NodeType.LIMITATION, c.text)
                add_edge(pid, lid, E.LIMITED_BY)
            if c.is_open_question():
                oid = f"openq:{c.claim_id}"
                add_node(oid, NodeType.OPEN_QUESTION, c.text)
                add_edge(pid, oid, E.LEAVES_OPEN)
            # intra-paper support: a supporting-class claim
            # supports the paper's primary claim
            if (
                primary is not None
                and c.claim_id != primary
                and c.claim_class in _SUPPORT_CLASSES
            ):
                add_edge(
                    cid, f"claim:{primary}", E.SUPPORTS,
                )
        for m in p.methods:
            mid = f"method:{m}"
            add_node(mid, NodeType.METHOD, m)
            add_edge(pid, mid, E.REUSES_METHOD)
        for mt in p.metrics:
            mtid = f"metric:{mt}"
            add_node(mtid, NodeType.METRIC, mt)
            add_edge(pid, mtid, E.REUSES_METRIC)
        for ds in p.datasets:
            dsid = f"dataset:{ds}"
            add_node(dsid, NodeType.DATASET, ds)
            add_edge(pid, dsid, E.DERIVED_FROM)
        for ext in p.extends:
            add_edge(pid, f"paper:{ext}", E.EXTENDS)

    # cross-paper conflicts -> connect the two papers' primary
    # claims (a conflict is made visible, never adjudicated)
    by_id = {p.paper_id: p for p in papers()}
    for p in papers():
        src_primary = _primary_claim_id(p)
        for other in p.conflicts:
            other_primary = _primary_claim_id(by_id[other])
            if src_primary and other_primary:
                add_edge(
                    f"claim:{src_primary}",
                    f"claim:{other_primary}",
                    E.CONFLICTS_WITH,
                )

    node_tuple = tuple(
        sorted(nodes.values(), key=lambda n: n.sort_key())
    )
    edge_tuple = tuple(
        sorted(edges, key=lambda e: e.sort_key())
    )
    return node_tuple, edge_tuple


@lru_cache(maxsize=1)
def _build() -> tuple[tuple[Node, ...], tuple[Edge, ...]]:
    return _construct()


def nodes() -> tuple[Node, ...]:
    return _build()[0]


def edges() -> tuple[Edge, ...]:
    return _build()[1]


def nodes_of_type(node_type: str) -> tuple[Node, ...]:
    return tuple(n for n in nodes() if n.node_type == node_type)


def edges_of_type(edge_type: str) -> tuple[Edge, ...]:
    return tuple(e for e in edges() if e.edge_type == edge_type)


def _signature_of(pair) -> str:
    n, e = pair
    parts = [f"N|{x.node_type}|{x.node_id}" for x in n]
    parts += [
        f"E|{x.edge_type}|{x.source}|{x.target}" for x in e
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def graph_signature() -> str:
    return _signature_of(_build())


def determinism_signatures() -> tuple[str, str]:
    return (_signature_of(_construct()), _signature_of(_construct()))


__all__ = [
    "determinism_signatures",
    "edges",
    "edges_of_type",
    "graph_signature",
    "nodes",
    "nodes_of_type",
]
