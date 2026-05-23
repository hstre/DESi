"""v3.47 — per-GAP cause attribution.

Uses the v3.32 ``classify_trajectory`` machinery to
record each GAP case's primary and secondary cause
classes. The plateau cohort is anchored at
``CONFIDENCE_OSCILLATION``; if the GAP cohort
dominates a different cause class, that supports the
"separate failure category" reading.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from ..gap_detected.extractor import terminal_gap_cases
from ..trajectory_root_cause.classifier import (
    classify_trajectory,
)


PLATEAU_PRIMARY_CAUSE = "CONFIDENCE_OSCILLATION"


@dataclass(frozen=True)
class GapCauseRecord:
    trajectory_id: str
    primary_cause: str
    secondary_causes: tuple[str, ...]
    matches_plateau_cause: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "primary_cause": self.primary_cause,
            "secondary_causes":
                list(self.secondary_causes),
            "matches_plateau_cause":
                self.matches_plateau_cause,
        }


def _trajs_by_id() -> dict[str, Trajectory]:
    return {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }


def classify_gap_cohort() -> tuple[GapCauseRecord, ...]:
    trajs = _trajs_by_id()
    out: list[GapCauseRecord] = []
    for c in terminal_gap_cases():
        cls = classify_trajectory(
            trajs[c.trajectory_id],
        )
        out.append(GapCauseRecord(
            trajectory_id=c.trajectory_id,
            primary_cause=cls.primary_cause,
            secondary_causes=cls.secondary_causes,
            matches_plateau_cause=(
                cls.primary_cause
                == PLATEAU_PRIMARY_CAUSE
            ),
        ))
    return tuple(out)


def cause_distribution() -> dict[str, int]:
    return dict(Counter(
        c.primary_cause for c in classify_gap_cohort()
    ))


__all__ = [
    "GapCauseRecord", "PLATEAU_PRIMARY_CAUSE",
    "cause_distribution", "classify_gap_cohort",
]
