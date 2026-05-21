"""v30.0 - deterministic evolution-memory graph construction.

Builds the read-only evolution history graph from the recorded
mutations and decisions: mutation ideas, the agents that proposed
them, the modules they target, their provenance claims, the
concept gate and generation that evaluated them, their decisions,
and the consequences (accepted metric / produced branch, or
rejected risk / violated invariant). Rejected ideas are kept.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache

from .decisions import DECISION_ACCEPT, decisions
from .memory_schema import Edge, Node, NodeType
from .mutations import mutations

_SANDBOX_BASE = "sandbox_base"
_GENERATION = "gen_0"
_GATE = "self_improvement_gate"


def _construct() -> tuple[tuple[Node, ...], tuple[Edge, ...]]:
    nodes: dict[str, Node] = {}
    edges: set[Edge] = set()

    def add(nid: str, ntype: NodeType, label: str) -> str:
        if nid not in nodes:
            nodes[nid] = Node(nid, ntype.value, label)
        return nid

    def link(src: str, dst: str, etype) -> None:
        edges.add(Edge(src, dst, etype.value))

    from .memory_schema import EdgeType as E

    add(f"generation:{_GENERATION}", NodeType.GENERATION,
        "evolution generation 0")
    add(f"gate:{_GATE}", NodeType.CONCEPT_GATE,
        "self-improvement concept gate")
    add(f"branch:{_SANDBOX_BASE}", NodeType.BRANCH,
        "isolated sandbox base (never main)")

    decision_by_mut = {d.mutation_id: d for d in decisions()}

    for m in mutations():
        mid = f"mutation:{m.mutation_id}"
        add(mid, NodeType.MUTATION_IDEA,
            f"{m.proposed_by} -> {m.target_area}")
        # provenance / proposer / target
        aid = f"agent:{m.proposed_by}"
        add(aid, NodeType.AGENT, m.proposed_by)
        link(mid, aid, E.PROPOSED_BY)
        modid = f"module:{m.target_area}"
        add(modid, NodeType.MODULE, m.target_area)
        link(mid, modid, E.TARGETS)
        if m.source_claim_id:
            pid = f"paperclaim:{m.source_claim_id}"
            add(pid, NodeType.PAPER_CLAIM, m.source_claim_id)
            link(mid, pid, E.DERIVED_FROM)
        # evaluated by the gate and the generation
        link(mid, f"gate:{_GATE}", E.EVALUATED_BY)
        link(mid, f"generation:{_GENERATION}", E.EVALUATED_BY)
        # decision
        d = decision_by_mut[m.mutation_id]
        did = f"decision:{d.decision_id}"
        add(did, NodeType.DECISION, d.outcome)
        link(did, mid, E.EVALUATED_BY)
        # consequence
        if d.outcome == DECISION_ACCEPT:
            metid = f"metric:{m.evolution_metric or 'governance_safe'}"
            add(metid, NodeType.EVOLUTION_METRIC,
                m.evolution_metric or "governance_safe")
            link(mid, metid, E.ACCEPTED_BECAUSE)
            if m.produced_branch:
                bid = f"branch:{m.produced_branch}"
                add(bid, NodeType.BRANCH, m.produced_branch)
                link(mid, bid, E.PRODUCED_BRANCH)
                link(bid, f"branch:{_SANDBOX_BASE}",
                     E.DESCENDS_FROM)
                if m.regression_run:
                    rid = f"regression:{m.regression_run}"
                    add(rid, NodeType.REGRESSION_RUN,
                        m.regression_run)
                    link(bid, rid, E.VALIDATED_BY)
        else:
            riskid = f"risk:{d.reason}"
            add(riskid, NodeType.RISK, d.reason)
            link(mid, riskid, E.REJECTED_BECAUSE)
            invid = f"invariant:{d.invariant}"
            add(invid, NodeType.INVARIANT, d.invariant)
            link(mid, invid, E.INVALIDATED_BY)

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


def out_edges(node_id: str) -> tuple[Edge, ...]:
    return tuple(e for e in edges() if e.source == node_id)


def mutation_edge_kinds(mutation_id: str) -> frozenset[str]:
    mid = f"mutation:{mutation_id}"
    return frozenset(e.edge_type for e in out_edges(mid))


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
    "mutation_edge_kinds",
    "nodes",
    "nodes_of_type",
    "out_edges",
]
