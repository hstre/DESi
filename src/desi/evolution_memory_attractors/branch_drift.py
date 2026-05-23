"""v30.2 - branch drift and convergence.

Observes how proposal branches relate through DESCENDS_FROM
edges: their convergence onto the shared sandbox base and the
drift depth. All proposal branches stay anchored to the sandbox
base (no drift toward main), which keeps drift observable and
bounded.
"""
from __future__ import annotations

from desi.evolution_memory import edges_of_type, nodes_of_type
from desi.evolution_memory.memory_schema import NodeType


def branch_nodes() -> tuple[str, ...]:
    return tuple(sorted(
        n.node_id for n in nodes_of_type(NodeType.BRANCH.value)
    ))


def descends_edges() -> tuple[tuple[str, str], ...]:
    return tuple(sorted(
        (e.source, e.target)
        for e in edges_of_type("DESCENDS_FROM")
    ))


def converges_on_base() -> tuple[str, ...]:
    """Proposal branches that descend from the sandbox base."""
    return tuple(sorted(
        src for src, dst in descends_edges()
        if dst.endswith("sandbox_base")
    ))


def branches_targeting_main() -> tuple[str, ...]:
    return tuple(sorted(
        b for b in branch_nodes() if b.endswith(":main")
    ))


def drift_visibility() -> float:
    """1.0 iff every non-base branch's lineage is observable
    (descends from a known base) and none drifts toward main."""
    bs = [b for b in branch_nodes()
          if not b.endswith("sandbox_base")]
    if not bs:
        return 1.0
    converging = set(converges_on_base())
    observable = sum(1 for b in bs if b in converging)
    if branches_targeting_main():
        return 0.0
    return round(observable / len(bs), 6)


__all__ = [
    "branch_nodes",
    "branches_targeting_main",
    "converges_on_base",
    "descends_edges",
    "drift_visibility",
]
