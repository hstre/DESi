"""v3.76 — blind multi-claim recovery.

Hide a closed subset of the v3.73 test claim set,
let DESi infer:

* how many missing claims (approximate)
* where (region centroids)
* which role (small cluster = bridge, large cluster
  = high / redundant)

DESi sees only the orphan leakage pattern, not the
hidden ids.

Hidden set: {BRIDGE, HIGH, REDUNDANT} — three claims
chosen so the orphan signal contains TWO distinct
coverage regions (HIGH and REDUNDANT covered the same
121-leakage set; BRIDGE covered a disjoint 12-leakage
set).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..field_leakage.census import (
    collect_leakage_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..missing_claim.remove import (
    PROBE_RADIUS, TEST_CLAIM_SET,
    _gather_vectors, baseline_coverage,
)


CLUSTER_DISTANCE_THRESHOLD: float = 1.0
"""Maximum within-cluster pairwise distance for the
orphan single-link clustering. 1.0 separates the
12-leakage and 121-leakage orphan regions cleanly in
the v3.50 corpus."""

HIDDEN_SUBSET: tuple[str, ...] = (
    "v23:R5_02",   # bridge
    "v23:R5_04",   # high
    "v314:D02",    # redundant (duplicates high)
)
HIDDEN_ROLES: dict[str, str] = {
    "v23:R5_02": "bridge",
    "v23:R5_04": "high_coverage",
    "v314:D02":  "redundant",
}


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def visible_set() -> tuple[str, ...]:
    set_ids = tuple(aid for aid, _ in TEST_CLAIM_SET)
    return tuple(
        a for a in set_ids if a not in HIDDEN_SUBSET
    )


def orphan_indices() -> tuple[int, ...]:
    plat_vecs, leak_vecs = _gather_vectors()
    set_ids = tuple(aid for aid, _ in TEST_CLAIM_SET)
    baseline = baseline_coverage(
        set_ids, plat_vecs, leak_vecs, PROBE_RADIUS,
    )
    visible = visible_set()
    new_cov = baseline_coverage(
        visible, plat_vecs, leak_vecs, PROBE_RADIUS,
    )
    return tuple(sorted(baseline - new_cov))


@dataclass(frozen=True)
class OrphanCluster:
    cluster_id: int
    member_indices: tuple[int, ...]
    centroid: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "member_indices":
                list(self.member_indices),
            "centroid": list(self.centroid),
        }


def _single_link_clusters(
    points: list[tuple[int, tuple[float, ...]]],
    threshold: float,
) -> list[list[int]]:
    n = len(points)
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

    for i in range(n):
        for j in range(i + 1, n):
            if (
                euclidean(points[i][1], points[j][1])
                <= threshold
            ):
                union(i, j)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(
            points[i][0],
        )
    return [
        sorted(v) for v in sorted(
            groups.values(), key=lambda g: g[0],
        )
    ]


def cluster_orphans() -> tuple[OrphanCluster, ...]:
    _, leak_vecs = _gather_vectors()
    indices = orphan_indices()
    points = [(i, leak_vecs[i]) for i in indices]
    groups = _single_link_clusters(
        points, CLUSTER_DISTANCE_THRESHOLD,
    )
    out: list[OrphanCluster] = []
    for cid, members in enumerate(groups):
        if not members:
            continue
        member_vecs = [leak_vecs[i] for i in members]
        d = len(member_vecs[0])
        centroid = tuple(
            _round(
                sum(v[k] for v in member_vecs)
                / len(member_vecs),
            )
            for k in range(d)
        )
        out.append(OrphanCluster(
            cluster_id=cid,
            member_indices=tuple(members),
            centroid=centroid,
        ))
    return tuple(out)


__all__ = [
    "CLUSTER_DISTANCE_THRESHOLD", "HIDDEN_ROLES",
    "HIDDEN_SUBSET", "OrphanCluster",
    "cluster_orphans", "orphan_indices",
    "visible_set",
]
