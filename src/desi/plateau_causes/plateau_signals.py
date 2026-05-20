"""v3.32 — per-plateau feature vector.

Six features summarising each plateau trajectory:

* branch_cost_max         — peak branch_cost across the
  trajectory.
* branch_cost_final       — branch_cost at the audit step.
* novelty_max             — peak novelty across the
  trajectory.
* novelty_final           — novelty at the audit step.
* confidence_variance     — variance of confidence over
  all states.
* frame_flip_count        — count of frame_id changes
  between non-zero declared frames.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import Trajectory
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)


_IDX_FRAME      = DIMENSION_NAMES.index("frame_id")
_IDX_CONF       = DIMENSION_NAMES.index("confidence")
_IDX_BRANCH     = DIMENSION_NAMES.index("branch_cost")
_IDX_NOVELTY    = DIMENSION_NAMES.index("novelty")


@dataclass(frozen=True)
class PlateauFeatures:
    trajectory_id: str
    source: str
    branch_cost_max: float
    branch_cost_final: float
    novelty_max: float
    novelty_final: float
    confidence_variance: float
    frame_flip_count: int

    def feature_vector(self) -> tuple[float, ...]:
        return (
            self.branch_cost_max,
            self.branch_cost_final,
            self.novelty_max,
            self.novelty_final,
            self.confidence_variance,
            float(self.frame_flip_count),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source,
            "branch_cost_max": self.branch_cost_max,
            "branch_cost_final":
                self.branch_cost_final,
            "novelty_max": self.novelty_max,
            "novelty_final": self.novelty_final,
            "confidence_variance":
                self.confidence_variance,
            "frame_flip_count": self.frame_flip_count,
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    m = sum(values) / len(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def extract_features(
    traj: Trajectory,
) -> PlateauFeatures:
    branches = [
        s.to_tuple()[_IDX_BRANCH] for s in traj.states
    ]
    novelty = [
        s.to_tuple()[_IDX_NOVELTY] for s in traj.states
    ]
    conf = [
        s.to_tuple()[_IDX_CONF] for s in traj.states
    ]
    frames = [
        s.to_tuple()[_IDX_FRAME] for s in traj.states
    ]
    flips = 0
    for i in range(len(frames) - 1):
        a, b = frames[i], frames[i + 1]
        if a != b and a > 0.0 and b > 0.0:
            flips += 1
    return PlateauFeatures(
        trajectory_id=traj.trajectory_id,
        source=traj.source.value,
        branch_cost_max=_round(max(branches)),
        branch_cost_final=_round(
            branches[-1] if branches else 0.0,
        ),
        novelty_max=_round(max(novelty)),
        novelty_final=_round(
            novelty[-1] if novelty else 0.0,
        ),
        confidence_variance=_round(_variance(conf)),
        frame_flip_count=flips,
    )


__all__ = ["PlateauFeatures", "extract_features"]
