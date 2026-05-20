"""v3.79 — coverage-equivalence primitives.

Two plateau anchors are EXACT DUPLICATES if their
coverage sets are bit-identical. The corpus's exact-
duplicate partition forms the closed set of
"redundancy classes". Partial overlap is computed
across classes as ``|A ∩ B| / max(|A|, |B|)``.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


PROBE_RADIUS: float = 3.5


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class RedundancyClass:
    class_id: int
    coverage_size: int
    members: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "class_id": self.class_id,
            "coverage_size": self.coverage_size,
            "members": list(self.members),
        }


def per_anchor_coverages(
) -> dict[str, frozenset[int]]:
    plats = {
        t.trajectory_id: trajectory_vector(t.states)
        for t in collect_plateau_anchors()
    }
    leaks = [
        trajectory_vector(t.states)
        for t in collect_leakage_trajectories()
    ]
    return {
        pid: frozenset(
            i for i, l in enumerate(leaks)
            if euclidean(av, l) <= PROBE_RADIUS
        )
        for pid, av in plats.items()
    }


def redundancy_classes() -> tuple[
    RedundancyClass, ...,
]:
    covs = per_anchor_coverages()
    groups: dict[frozenset[int], list[str]] = (
        defaultdict(list)
    )
    for pid, c in covs.items():
        groups[c].append(pid)
    # Sort classes by descending member count, then by
    # descending coverage size for determinism.
    sorted_items = sorted(
        groups.items(),
        key=lambda kv: (
            -len(kv[1]), -len(kv[0]), kv[1][0],
        ),
    )
    return tuple(
        RedundancyClass(
            class_id=i,
            coverage_size=len(cov),
            members=tuple(sorted(members)),
        )
        for i, (cov, members) in enumerate(
            sorted_items,
        )
    )


def exact_duplicate_count(
    classes: tuple[RedundancyClass, ...],
) -> int:
    """Classes with more than one member (= exact
    duplicates exist)."""
    return sum(
        1 for c in classes if len(c.members) > 1
    )


def largest_redundancy_class(
    classes: tuple[RedundancyClass, ...],
) -> int:
    if not classes:
        return 0
    return max(len(c.members) for c in classes)


@dataclass(frozen=True)
class PartialOverlap:
    class_a_id: int
    class_b_id: int
    overlap_size: int
    overlap_fraction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "class_a_id": self.class_a_id,
            "class_b_id": self.class_b_id,
            "overlap_size": self.overlap_size,
            "overlap_fraction":
                self.overlap_fraction,
        }


def partial_overlaps(
    classes: tuple[RedundancyClass, ...],
) -> tuple[PartialOverlap, ...]:
    """Cross-class pairwise overlaps. An overlap with
    fraction == 0 means the classes are disjoint;
    fraction == 1 means equal (which would mean they
    are the same class, so excluded)."""
    covs = per_anchor_coverages()
    # Pick a representative coverage per class.
    rep_cov = {
        c.class_id: covs.get(c.members[0], frozenset())
        for c in classes
    }
    out: list[PartialOverlap] = []
    for i in range(len(classes)):
        for j in range(i + 1, len(classes)):
            a = rep_cov[classes[i].class_id]
            b = rep_cov[classes[j].class_id]
            inter = a & b
            larger = max(len(a), len(b))
            frac = (
                _round(len(inter) / larger)
                if larger > 0 else 0.0
            )
            out.append(PartialOverlap(
                class_a_id=classes[i].class_id,
                class_b_id=classes[j].class_id,
                overlap_size=len(inter),
                overlap_fraction=frac,
            ))
    return tuple(out)


def partial_overlap_count(
    overlaps: tuple[PartialOverlap, ...],
) -> int:
    return sum(
        1 for o in overlaps
        if 0 < o.overlap_fraction < 1
    )


__all__ = [
    "PROBE_RADIUS", "PartialOverlap",
    "RedundancyClass",
    "exact_duplicate_count",
    "largest_redundancy_class",
    "partial_overlap_count", "partial_overlaps",
    "per_anchor_coverages",
    "redundancy_classes",
]
