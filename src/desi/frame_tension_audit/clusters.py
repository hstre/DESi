"""Aufgaben 5 + 6 — cluster the FALSE / AMBIGUOUS cases and gate
each cluster on patchability.

Clustering key: (outer_frame, inner_frame, failure_cause). Only
FALSE_TENSION and AMBIGUOUS_TENSION cases participate.

A cluster is patchable only when **all** of:

* ``cluster_size >= 3``
* ``failure_cause`` is unique (every member shares the same cause)
* ``contamination_risk == 0`` (decided in ``contamination.py``)
* none of the v3.9 manipulation cases would be absorbed (also
  decided in ``contamination.py``)
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import TensionAuditClass, TensionFailureCause
from .splitter import TensionAuditOutcome


MIN_PATCHABLE_SIZE: int = 3


@dataclass(frozen=True)
class TensionCluster:
    cluster_id: str
    outer_frame: str
    inner_frame: str
    failure_cause: TensionFailureCause
    case_ids: tuple[str, ...]

    @property
    def size(self) -> int:
        return len(self.case_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_id": self.cluster_id,
            "outer_frame": self.outer_frame,
            "inner_frame": self.inner_frame,
            "failure_cause": self.failure_cause.value,
            "case_ids": list(self.case_ids),
            "size": self.size,
        }


@dataclass(frozen=True)
class ClusterSummary:
    cluster_count: int
    largest_cluster_size: int
    dominant_failure_cause: str | None
    dominant_frame_pair: tuple[str, str] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster_count": self.cluster_count,
            "largest_cluster_size": self.largest_cluster_size,
            "dominant_failure_cause": self.dominant_failure_cause,
            "dominant_frame_pair": (
                list(self.dominant_frame_pair)
                if self.dominant_frame_pair else None
            ),
        }


def build_clusters(
    outcomes: tuple[TensionAuditOutcome, ...],
) -> tuple[TensionCluster, ...]:
    bucket: dict[tuple[str, str, str], list[str]] = {}
    for o in outcomes:
        if o.audit_class is TensionAuditClass.TRUE_TENSION:
            continue
        outer = o.target.outer_frame or "none"
        inner = o.target.inner_frame or "none"
        cause = (
            o.failure_cause.value if o.failure_cause
            else TensionFailureCause.UNKNOWN.value
        )
        key = (outer, inner, cause)
        bucket.setdefault(key, []).append(o.target.case_id)

    clusters: list[TensionCluster] = []
    for (outer, inner, cause), ids in sorted(bucket.items()):
        clusters.append(TensionCluster(
            cluster_id=f"K_{outer}__{inner}__{cause}",
            outer_frame=outer,
            inner_frame=inner,
            failure_cause=TensionFailureCause(cause),
            case_ids=tuple(sorted(ids)),
        ))
    return tuple(clusters)


def summarise_clusters(
    clusters: tuple[TensionCluster, ...],
) -> ClusterSummary:
    if not clusters:
        return ClusterSummary(
            cluster_count=0,
            largest_cluster_size=0,
            dominant_failure_cause=None,
            dominant_frame_pair=None,
        )
    largest = max(clusters, key=lambda c: c.size)
    cause_counts: dict[str, int] = {}
    pair_counts: dict[tuple[str, str], int] = {}
    for c in clusters:
        cause_counts[c.failure_cause.value] = (
            cause_counts.get(c.failure_cause.value, 0) + c.size
        )
        pair = (c.outer_frame, c.inner_frame)
        pair_counts[pair] = pair_counts.get(pair, 0) + c.size
    dom_cause = max(cause_counts.items(), key=lambda kv: kv[1])[0]
    dom_pair = max(pair_counts.items(), key=lambda kv: kv[1])[0]
    return ClusterSummary(
        cluster_count=len(clusters),
        largest_cluster_size=largest.size,
        dominant_failure_cause=dom_cause,
        dominant_frame_pair=dom_pair,
    )


__all__ = [
    "ClusterSummary",
    "MIN_PATCHABLE_SIZE",
    "TensionCluster",
    "build_clusters",
    "summarise_clusters",
]
