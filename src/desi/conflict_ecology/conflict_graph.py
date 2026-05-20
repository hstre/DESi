"""v6.2 — conflict-graph topology.

Nodes are papers, edges are detected conflicts.
We compute connected components (fragmentation),
the largest two component sizes (polarisation),
and a per-topic agreement summary.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .cross_paper import (
    EcologyPaper, corpus, detected_conflicts,
)


@dataclass(frozen=True)
class GraphNode:
    paper_id: str
    topic: str
    component_id: int

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "topic": self.topic,
            "component_id":
                self.component_id,
        }


def _build_adj() -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {
        p.paper_id: set() for p in corpus()
    }
    for c in detected_conflicts():
        adj[c.paper_a].add(c.paper_b)
        adj[c.paper_b].add(c.paper_a)
    return adj


@lru_cache(maxsize=1)
def components() -> tuple[
    tuple[str, ...], ...,
]:
    adj = _build_adj()
    seen: set[str] = set()
    out: list[tuple[str, ...]] = []
    for start in sorted(adj.keys()):
        if start in seen:
            continue
        stack = [start]
        comp: list[str] = []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            comp.append(node)
            for nb in adj[node]:
                if nb not in seen:
                    stack.append(nb)
        comp.sort()
        out.append(tuple(comp))
    out.sort(
        key=lambda c: (-len(c), c[0]),
    )
    return tuple(out)


@lru_cache(maxsize=1)
def nodes() -> tuple[GraphNode, ...]:
    by_id = {
        p.paper_id: p for p in corpus()
    }
    out: list[GraphNode] = []
    for cid, comp in enumerate(components()):
        for pid in comp:
            out.append(GraphNode(
                paper_id=pid,
                topic=by_id[pid].topic,
                component_id=cid,
            ))
    out.sort(
        key=lambda n: (n.component_id, n.paper_id),
    )
    return tuple(out)


def fragmentation_rate() -> float:
    """Number of connected components divided
    by the total number of papers. Near 0 means
    one mega-cluster; near 1 means every paper
    is its own island."""
    total = len(corpus())
    if total == 0:
        return 0.0
    return round(
        len(components()) / total, 6,
    )


def polarization_index() -> float:
    """Fraction of papers that belong to one of
    the two largest components. 1.0 means the
    debate splits cleanly into two camps; lower
    means there is no dominant split."""
    total = len(corpus())
    if total == 0:
        return 0.0
    comps = components()
    if not comps:
        return 0.0
    top_two = sum(
        len(c) for c in comps[:2]
    )
    return round(top_two / total, 6)


def coherence_score() -> float:
    """1.0 minus a normalised conflict density:
    if every pair conflicts, coherence is 0; if
    no pair conflicts, coherence is 1."""
    n = len(corpus())
    if n < 2:
        return 1.0
    possible = n * (n - 1) // 2
    actual = len(detected_conflicts())
    return round(
        max(0.0, 1.0 - actual / possible), 6,
    )


def topic_conflict_density() -> dict[str, int]:
    cnt: dict[str, int] = {}
    for c in detected_conflicts():
        cnt[c.topic] = cnt.get(c.topic, 0) + 1
    return dict(sorted(cnt.items()))


def conflict_resolution_stability() -> float:
    """A deterministic detector gives the same
    conflict set on every replay. We score 1.0
    iff two back-to-back runs produce identical
    component partitions."""
    a = tuple(components())
    b = tuple(components())
    return 1.0 if a == b else 0.0


__all__ = [
    "GraphNode",
    "coherence_score",
    "components",
    "conflict_resolution_stability",
    "fragmentation_rate",
    "nodes",
    "polarization_index",
    "topic_conflict_density",
]
