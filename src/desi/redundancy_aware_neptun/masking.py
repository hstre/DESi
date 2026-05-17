"""v3.80 — class-level claim removal masking.

Builds two removal experiments:

* CLASS_REMOVAL: remove every member of a v3.79
  redundancy class at once. Expected to produce a
  perturbation equal to the class's coverage size.
* SINGLE_REMOVAL (within-class): remove ONE member
  of a class; the other members still cover the same
  region. Expected to produce 0 perturbation. This
  is the v3.73 single-anchor removal restated as a
  "redundant removal" comparator.

Comparing class_removal vs single_within_class is the
directive's gate1_recovered check.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..redundancy_masking.equivalence import (
    PROBE_RADIUS, RedundancyClass,
    per_anchor_coverages, redundancy_classes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _baseline_universe(
    covs: dict[str, frozenset[int]],
) -> frozenset[int]:
    out: set[int] = set()
    for c in covs.values():
        out |= c
    return frozenset(out)


@dataclass(frozen=True)
class ClassRemovalOutcome:
    class_id: int
    coverage_size: int
    members: tuple[str, ...]
    perturbation_magnitude: int
    single_member_perturbation: int

    def to_dict(self) -> dict[str, object]:
        return {
            "class_id": self.class_id,
            "coverage_size": self.coverage_size,
            "members": list(self.members),
            "perturbation_magnitude":
                self.perturbation_magnitude,
            "single_member_perturbation":
                self.single_member_perturbation,
        }


def class_removal_outcome(
    cls: RedundancyClass,
    covs: dict[str, frozenset[int]],
) -> ClassRemovalOutcome:
    baseline = _baseline_universe(covs)
    # Remove all class members at once
    reduced = {
        a: c for a, c in covs.items()
        if a not in cls.members
    }
    new_full = _baseline_universe(reduced)
    full_loss = len(baseline - new_full)
    # Remove ONE member only
    single_id = cls.members[0]
    reduced_single = {
        a: c for a, c in covs.items()
        if a != single_id
    }
    new_single = _baseline_universe(reduced_single)
    single_loss = len(baseline - new_single)
    return ClassRemovalOutcome(
        class_id=cls.class_id,
        coverage_size=cls.coverage_size,
        members=cls.members,
        perturbation_magnitude=full_loss,
        single_member_perturbation=single_loss,
    )


def all_class_removal_outcomes(
) -> tuple[ClassRemovalOutcome, ...]:
    covs = per_anchor_coverages()
    return tuple(
        class_removal_outcome(c, covs)
        for c in redundancy_classes()
    )


__all__ = [
    "ClassRemovalOutcome",
    "all_class_removal_outcomes",
    "class_removal_outcome",
]
