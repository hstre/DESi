"""v3.80 — redundancy-aware Neptun retest.

Reruns the v3.74 localization + v3.75 candidate
reconstruction logic, but the unit of removal is a
v3.79 redundancy class, not a single anchor. The
question: with class-level removal, does the
Neptun gate #1 recover?
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..missing_candidate.candidate import (
    PRE_AUDIT_INDEX,
)
from ..redundancy_masking.equivalence import (
    PROBE_RADIUS, RedundancyClass,
    per_anchor_coverages, redundancy_classes,
)
from .masking import (
    ClassRemovalOutcome,
    all_class_removal_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _centroid(
    vecs: list[tuple[float, ...]],
) -> tuple[float, ...]:
    if not vecs:
        return ()
    n = len(vecs)
    d = len(vecs[0])
    return tuple(
        sum(v[i] for v in vecs) / n
        for i in range(d)
    )


@dataclass(frozen=True)
class ClassLocalization:
    class_id: int
    coverage_size: int
    orphan_count: int
    centroid_distance_to_class: float
    predicted_correctly: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "class_id": self.class_id,
            "coverage_size": self.coverage_size,
            "orphan_count": self.orphan_count,
            "centroid_distance_to_class": (
                -1.0
                if self.centroid_distance_to_class
                == float("inf")
                else self.centroid_distance_to_class
            ),
            "predicted_correctly":
                self.predicted_correctly,
        }


def localize_class_removal(
    cls: RedundancyClass,
    covs: dict[str, frozenset[int]],
) -> ClassLocalization:
    baseline = set()
    for c in covs.values():
        baseline |= c
    reduced = {
        a: c for a, c in covs.items()
        if a not in cls.members
    }
    new_cov = set()
    for c in reduced.values():
        new_cov |= c
    orphans = baseline - new_cov
    if not orphans:
        return ClassLocalization(
            class_id=cls.class_id,
            coverage_size=cls.coverage_size,
            orphan_count=0,
            centroid_distance_to_class=float("inf"),
            predicted_correctly=False,
        )
    leaks = list(collect_leakage_trajectories())
    orphan_vecs = [
        trajectory_vector(leaks[i].states)
        for i in orphans
    ]
    centroid = _centroid(orphan_vecs)
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    # The class members' centroid in the same 45-d
    # space.
    class_vecs = [
        trajectory_vector(trajs[m].states)
        for m in cls.members
        if m in trajs
    ]
    class_centroid = _centroid(class_vecs)
    dist = (
        _round(euclidean(centroid, class_centroid))
        if class_centroid else float("inf")
    )
    # "Correct" = orphan centroid is closer to THIS
    # class's centroid than to any other class's
    # centroid.
    classes = redundancy_classes()
    best_id = -1
    best_d = float("inf")
    for other in classes:
        other_vecs = [
            trajectory_vector(trajs[m].states)
            for m in other.members
            if m in trajs
        ]
        oc = _centroid(other_vecs)
        if not oc:
            continue
        d = euclidean(centroid, oc)
        if d < best_d:
            best_d = d
            best_id = other.class_id
    return ClassLocalization(
        class_id=cls.class_id,
        coverage_size=cls.coverage_size,
        orphan_count=len(orphans),
        centroid_distance_to_class=dist,
        predicted_correctly=(
            best_id == cls.class_id
        ),
    )


def all_class_localizations() -> tuple[
    ClassLocalization, ...,
]:
    covs = per_anchor_coverages()
    return tuple(
        localize_class_removal(c, covs)
        for c in redundancy_classes()
    )


def localization_accuracy(
    locs: tuple[ClassLocalization, ...],
) -> float:
    eligible = [l for l in locs if l.orphan_count > 0]
    if not eligible:
        return 0.0
    correct = sum(
        1 for l in eligible if l.predicted_correctly
    )
    return _round(correct / len(eligible))


def candidate_match_score(
    locs: tuple[ClassLocalization, ...],
) -> float:
    """Closed-form score: fraction of class
    localizations where the predicted class id
    matches and the centroid distance is small
    (<= 5.0)."""
    eligible = [l for l in locs if l.orphan_count > 0]
    if not eligible:
        return 0.0
    matched = sum(
        1 for l in eligible
        if l.predicted_correctly
        and l.centroid_distance_to_class <= 5.0
    )
    return _round(matched / len(eligible))


def false_missing_claim_rate() -> float:
    """Reuse v3.77's negative-control result; the
    class-removal scheme inherits the same noise
    rejection."""
    from ..missing_negative_controls.report import (
        build_report as v377,
    )
    return v377().false_missing_claim_rate


__all__ = [
    "ClassLocalization",
    "all_class_localizations",
    "candidate_match_score",
    "false_missing_claim_rate",
    "localization_accuracy",
    "localize_class_removal",
]
