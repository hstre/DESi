"""Cluster + frame-specific breakdown — Aufgaben 3 + 4."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from ..frames import FrameKind
from .classes import FrameFailureClass
from .classifier import classify
from .extractor import FrameFailureRecord


@dataclass(frozen=True)
class FailureCluster:
    cluster_id: str
    failure_class: FrameFailureClass
    expected_frame: FrameKind
    members: tuple[str, ...]   # case_ids

    @property
    def size(self) -> int:
        return len(self.members)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "failure_class": self.failure_class.value,
            "expected_frame": self.expected_frame.value,
            "members": list(self.members),
            "size": self.size,
        }


@dataclass(frozen=True)
class ClusterSummary:
    clusters: tuple[FailureCluster, ...]
    singletons: tuple[FailureCluster, ...]
    cluster_count: int
    largest_cluster_size: int
    singleton_count: int
    entropy_of_failure_distribution: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "clusters": [c.to_dict() for c in self.clusters],
            "singletons": [c.to_dict() for c in self.singletons],
            "cluster_count": self.cluster_count,
            "largest_cluster_size": self.largest_cluster_size,
            "singleton_count": self.singleton_count,
            "entropy_of_failure_distribution":
                self.entropy_of_failure_distribution,
        }


def _shannon_entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log2(p)
    return round(h, 6)


def build_clusters(
    failures: tuple[FrameFailureRecord, ...],
) -> ClusterSummary:
    # Cluster key = (failure_class, expected_frame). Aufgabe 3
    # minimum cluster size = 2.
    grouped: dict[
        tuple[FrameFailureClass, FrameKind], list[FrameFailureRecord]
    ] = {}
    for f in failures:
        key = (classify(f), f.expected_frame)
        grouped.setdefault(key, []).append(f)

    clusters: list[FailureCluster] = []
    singletons: list[FailureCluster] = []
    for (cls, frame), members in sorted(
        grouped.items(),
        key=lambda kv: (kv[0][0].value, kv[0][1].value),
    ):
        cluster_id = f"CL_{cls.value}__{frame.value}"
        sorted_ids = tuple(sorted(m.case_id for m in members))
        cluster = FailureCluster(
            cluster_id=cluster_id,
            failure_class=cls,
            expected_frame=frame,
            members=sorted_ids,
        )
        if cluster.size >= 2:
            clusters.append(cluster)
        else:
            singletons.append(cluster)

    distribution = Counter(classify(f) for f in failures)
    entropy = _shannon_entropy(distribution)

    return ClusterSummary(
        clusters=tuple(clusters),
        singletons=tuple(singletons),
        cluster_count=len(clusters),
        largest_cluster_size=(
            max((c.size for c in clusters), default=0)
        ),
        singleton_count=len(singletons),
        entropy_of_failure_distribution=entropy,
    )


# ---------------------------------------------------------------------------
# Frame-specific breakdown — Aufgabe 4
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrameBreakdown:
    frame: FrameKind
    total_failures: int
    dominant_failure_class: FrameFailureClass | None
    concentration_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame": self.frame.value,
            "total_failures": self.total_failures,
            "dominant_failure_class": (
                self.dominant_failure_class.value
                if self.dominant_failure_class else None
            ),
            "concentration_ratio": self.concentration_ratio,
        }


def per_frame_breakdown(
    failures: tuple[FrameFailureRecord, ...],
) -> tuple[FrameBreakdown, ...]:
    by_frame: dict[FrameKind, list[FrameFailureRecord]] = {}
    for f in failures:
        by_frame.setdefault(f.expected_frame, []).append(f)
    out: list[FrameBreakdown] = []
    for frame in sorted(by_frame, key=lambda f: f.value):
        members = by_frame[frame]
        c = Counter(classify(m) for m in members)
        if not c:
            continue
        dominant, dominant_count = max(
            c.items(), key=lambda kv: (kv[1], kv[0].value),
        )
        out.append(FrameBreakdown(
            frame=frame,
            total_failures=len(members),
            dominant_failure_class=dominant,
            concentration_ratio=round(dominant_count / len(members), 6),
        ))
    return tuple(out)


__all__ = [
    "ClusterSummary",
    "FailureCluster",
    "FrameBreakdown",
    "build_clusters",
    "per_frame_breakdown",
]
