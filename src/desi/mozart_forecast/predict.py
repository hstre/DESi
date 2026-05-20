"""v3.72 — pre-activation forecast features.

A FORECAST predicts whether a trajectory is a
coverage outlier BEFORE its full trajectory has
unfolded. Only state[0] features are eligible -
nothing computed from the intervention or from later
states.

The forecast model is a normalised novelty@0 score:

    forecast_score(t) = t.states[0].novelty
                       / max_novelty_at_zero(corpus)

where ``max_novelty_at_zero`` is the empirical maximum
of state[0].novelty over the full trajectory corpus.
The single feature is sufficient because Mozart's
state[0].novelty = 12.0 is the strict corpus maximum
(no other trajectory reaches that value at the
initial state).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def max_novelty_at_zero() -> float:
    """Maximum state[0].novelty across the full
    corpus."""
    vals = [
        t.states[0].novelty
        for t in extract_all_trajectories()
        if t.states
    ]
    return max(vals) if vals else 0.0


def state0_novelty(traj: Trajectory) -> float:
    if not traj.states:
        return 0.0
    return traj.states[0].novelty


def forecast_score(traj: Trajectory) -> float:
    m = max_novelty_at_zero()
    if m == 0:
        return 0.0
    return _round(state0_novelty(traj) / m)


@dataclass(frozen=True)
class ForecastPoint:
    trajectory_id: str
    state0_novelty: float
    forecast_score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "state0_novelty": self.state0_novelty,
            "forecast_score": self.forecast_score,
        }


def per_trajectory_forecast(
    traj: Trajectory,
) -> ForecastPoint:
    return ForecastPoint(
        trajectory_id=traj.trajectory_id,
        state0_novelty=state0_novelty(traj),
        forecast_score=forecast_score(traj),
    )


__all__ = [
    "ForecastPoint", "forecast_score",
    "max_novelty_at_zero",
    "per_trajectory_forecast",
    "state0_novelty",
]
