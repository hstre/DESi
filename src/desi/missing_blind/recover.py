"""v3.76 — blind recovery scoring.

For each detected orphan cluster, predict a role
based on cluster size:

* size  <= 50 → ``bridge``  (small, unique coverage)
* size  > 50  → ``high_or_redundant``  (large, the
  HIGH/REDUNDANT pair's joint coverage)

Then evaluate:

* ``missing_count_error`` = |predicted_distinct_regions
  - actual_distinct_regions|  (HIGH and REDUNDANT
  count as one region because their coverage is
  identical)
* ``region_recall``        = correctly-recovered
  distinct regions / actual distinct regions
* ``role_recall``          = correctly-classified
  cluster role labels / total cluster labels
* ``false_reconstruction_rate`` = clusters that
  don't match any actual hidden region / total
  clusters
"""
from __future__ import annotations

from dataclasses import dataclass

from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..missing_claim.remove import _gather_vectors
from .blind import (
    CLUSTER_DISTANCE_THRESHOLD, HIDDEN_ROLES,
    HIDDEN_SUBSET, OrphanCluster, cluster_orphans,
)


CLUSTER_SIZE_BRIDGE_CEILING: int = 50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _predicted_role(cluster: OrphanCluster) -> str:
    if len(cluster.member_indices) <= (
        CLUSTER_SIZE_BRIDGE_CEILING
    ):
        return "bridge"
    return "high_or_redundant"


def _hidden_distinct_regions() -> int:
    """HIGH and REDUNDANT share coverage; they
    count as one region. BRIDGE is its own
    region."""
    return 2


def _hidden_role_labels() -> tuple[str, ...]:
    """Canonical role labels per distinct hidden
    region. Order matches BRIDGE then HIGH/REDUNDANT
    cluster."""
    return ("bridge", "high_or_redundant")


@dataclass(frozen=True)
class ClusterAssignment:
    cluster_id: int
    cluster_size: int
    centroid: tuple[float, ...]
    predicted_role: str
    nearest_hidden_id: str
    nearest_distance: float
    correctly_matched: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_size": self.cluster_size,
            "centroid": list(self.centroid),
            "predicted_role": self.predicted_role,
            "nearest_hidden_id":
                self.nearest_hidden_id,
            "nearest_distance":
                self.nearest_distance,
            "correctly_matched":
                self.correctly_matched,
        }


def assign_clusters(
) -> tuple[ClusterAssignment, ...]:
    plat_vecs, _ = _gather_vectors()
    clusters = cluster_orphans()
    out: list[ClusterAssignment] = []
    for c in clusters:
        # Pick nearest hidden anchor by Euclidean
        best_id = ""
        best_d = float("inf")
        for hid in HIDDEN_SUBSET:
            av = plat_vecs.get(hid)
            if av is None:
                continue
            d = euclidean(c.centroid, av)
            if d < best_d:
                best_d = d
                best_id = hid
        predicted = _predicted_role(c)
        actual_role = HIDDEN_ROLES.get(
            best_id, "unknown",
        )
        # The cluster is "correctly matched" when the
        # predicted role-bucket is consistent with the
        # nearest hidden anchor's role.
        correct = (
            (
                predicted == "bridge"
                and actual_role == "bridge"
            )
            or (
                predicted == "high_or_redundant"
                and actual_role in (
                    "high_coverage", "redundant",
                )
            )
        )
        out.append(ClusterAssignment(
            cluster_id=c.cluster_id,
            cluster_size=len(c.member_indices),
            centroid=c.centroid,
            predicted_role=predicted,
            nearest_hidden_id=best_id,
            nearest_distance=_round(best_d),
            correctly_matched=correct,
        ))
    return tuple(out)


def predicted_distinct_regions(
    assignments: tuple[ClusterAssignment, ...],
) -> int:
    return len(assignments)


def missing_count_error(
    assignments: tuple[ClusterAssignment, ...],
) -> int:
    return abs(
        predicted_distinct_regions(assignments)
        - _hidden_distinct_regions(),
    )


def region_recall(
    assignments: tuple[ClusterAssignment, ...],
) -> float:
    """Fraction of true distinct regions that have at
    least one cluster correctly mapping to them."""
    actual = set(_hidden_role_labels())
    recovered: set[str] = set()
    for a in assignments:
        if a.correctly_matched:
            recovered.add(a.predicted_role)
    if not actual:
        return 0.0
    return _round(len(recovered) / len(actual))


def role_recall(
    assignments: tuple[ClusterAssignment, ...],
) -> float:
    if not assignments:
        return 0.0
    correct = sum(
        1 for a in assignments
        if a.correctly_matched
    )
    return _round(correct / len(assignments))


def false_reconstruction_rate(
    assignments: tuple[ClusterAssignment, ...],
) -> float:
    if not assignments:
        return 0.0
    incorrect = sum(
        1 for a in assignments
        if not a.correctly_matched
    )
    return _round(incorrect / len(assignments))


__all__ = [
    "CLUSTER_SIZE_BRIDGE_CEILING",
    "ClusterAssignment", "assign_clusters",
    "false_reconstruction_rate",
    "missing_count_error",
    "predicted_distinct_regions",
    "region_recall", "role_recall",
]
