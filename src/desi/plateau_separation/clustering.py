"""v3.38 — connectivity-based clustering.

Builds a 1-NN graph over the trajectory vectors and
counts connected components. If the two classes form
disjoint manifolds, ``manifold_count`` = 2 and the
component-label assignment matches the class labels.

Pure-Python union-find. No external clustering library.
"""
from __future__ import annotations

from dataclasses import dataclass

from .distance import euclidean


def _nearest_index(
    vectors: tuple[tuple[float, ...], ...], i: int,
) -> int:
    best_j = -1
    best_d = float("inf")
    for j in range(len(vectors)):
        if j == i:
            continue
        d = euclidean(vectors[i], vectors[j])
        if d < best_d:
            best_d = d
            best_j = j
    return best_j


def one_nn_edges(
    vectors: tuple[tuple[float, ...], ...],
) -> tuple[tuple[int, int], ...]:
    """For each item, an undirected edge to its nearest
    neighbour."""
    edges = set()
    for i in range(len(vectors)):
        j = _nearest_index(vectors, i)
        if j < 0:
            continue
        edges.add(tuple(sorted((i, j))))
    return tuple(sorted(edges))


def connected_components(
    n: int, edges: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, ...], ...]:
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for a, b in edges:
        union(a, b)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return tuple(
        tuple(sorted(v)) for v in sorted(
            groups.values(), key=lambda g: g[0],
        )
    )


@dataclass(frozen=True)
class ClusterAssignment:
    component_id: int
    member_ids: tuple[str, ...]
    member_classes: tuple[str, ...]
    is_pure: bool
    majority_class: str

    def to_dict(self) -> dict[str, object]:
        return {
            "component_id": self.component_id,
            "member_ids": list(self.member_ids),
            "member_classes": list(self.member_classes),
            "is_pure": self.is_pure,
            "majority_class": self.majority_class,
        }


def assign_clusters(
    items: tuple[tuple[str, str, tuple[float, ...]], ...],
) -> tuple[ClusterAssignment, ...]:
    vectors = tuple(v for _, _, v in items)
    edges = one_nn_edges(vectors)
    components = connected_components(len(items), edges)
    out: list[ClusterAssignment] = []
    for cid, comp in enumerate(components):
        ids = tuple(items[i][0] for i in comp)
        cls = tuple(items[i][1] for i in comp)
        counts: dict[str, int] = {}
        for c in cls:
            counts[c] = counts.get(c, 0) + 1
        majority = max(
            counts.items(), key=lambda kv: (kv[1], kv[0]),
        )[0]
        out.append(ClusterAssignment(
            component_id=cid, member_ids=ids,
            member_classes=cls,
            is_pure=len(set(cls)) == 1,
            majority_class=majority,
        ))
    return tuple(out)


__all__ = [
    "ClusterAssignment", "assign_clusters",
    "connected_components", "one_nn_edges",
]
