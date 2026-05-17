"""v3.32 — plateau cause distribution.

For every plateau trajectory, record its v3.28 primary
cause and any secondary causes. Aggregate the
distribution and identify the dominant class.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..epistemic_trajectory.extractor import Trajectory
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from ..trajectory_root_cause.classifier import (
    CauseAssignment, classify_trajectory,
)


@dataclass(frozen=True)
class CauseDistribution:
    primary: dict[str, int]
    secondary: dict[str, int]
    multi_cause_count: int
    dominant_primary: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "primary": dict(self.primary),
            "secondary": dict(self.secondary),
            "multi_cause_count": self.multi_cause_count,
            "dominant_primary": self.dominant_primary,
        }


def collect_assignments(
    trajectories: tuple[Trajectory, ...],
) -> tuple[CauseAssignment, ...]:
    pids = set(plateau_trajectory_ids())
    out = []
    for t in trajectories:
        if t.trajectory_id in pids:
            out.append(classify_trajectory(t))
    return tuple(out)


def compute_distribution(
    assignments: tuple[CauseAssignment, ...],
) -> CauseDistribution:
    primary = Counter(a.primary_cause for a in assignments)
    secondary = Counter()
    for a in assignments:
        for s in a.secondary_causes:
            secondary[s] += 1
    multi = sum(
        1 for a in assignments
        if a.secondary_causes
    )
    dominant = (
        primary.most_common(1)[0][0] if primary else None
    )
    return CauseDistribution(
        primary=dict(primary),
        secondary=dict(secondary),
        multi_cause_count=multi,
        dominant_primary=dominant,
    )


__all__ = [
    "CauseDistribution", "collect_assignments",
    "compute_distribution",
]
