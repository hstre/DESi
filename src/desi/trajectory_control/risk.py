"""v3.25 — trajectory-level risk metrics.

Five required measurements from the directive:

* ``cliff_proximity``       — minimum proximity (in
  steps) the observer reported across the trajectory.
* ``confidence_variance``   — variance of confidence
  across all states.
* ``branch_acceleration``   — max |2nd derivative of
  branch_cost|.
* ``oscillation_risk``      — fraction of transitions
  flagged as direction reversals.
* ``support_decay``         — max single-step drop in
  support_state.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from .observer import TrajectoryObservation
from .state import StepFeatures, compute_step_features


_IDX_CONF    = DIMENSION_NAMES.index("confidence")
_IDX_BRANCH  = DIMENSION_NAMES.index("branch_cost")
_IDX_SUPPORT = DIMENSION_NAMES.index("support_state")


@dataclass(frozen=True)
class TrajectoryRisk:
    trajectory_id: str
    cliff_proximity: int
    confidence_variance: float
    branch_acceleration: float
    oscillation_risk: float
    support_decay: float

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "cliff_proximity": self.cliff_proximity,
            "confidence_variance":
                self.confidence_variance,
            "branch_acceleration":
                self.branch_acceleration,
            "oscillation_risk": self.oscillation_risk,
            "support_decay": self.support_decay,
        }


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def compute_risk(
    states: tuple[StateVector, ...],
    features: tuple[StepFeatures, ...] | None = None,
    observation: TrajectoryObservation | None = None,
    *, trajectory_id: str = "",
) -> TrajectoryRisk:
    feats = features if features is not None else (
        compute_step_features(states)
    )

    if observation is not None and observation.predictions:
        proximities = [
            p.cliff_proximity for p in observation.predictions
        ]
        cliff_prox = min(proximities)
    else:
        cliff_prox = 99

    conf = [s.to_tuple()[_IDX_CONF] for s in states]
    conf_var = round(_variance(conf), 6)

    branch_jerks = [
        abs(f.branch_jerk) for f in feats
    ]
    branch_acc = round(
        max(branch_jerks) if branch_jerks else 0.0, 6,
    )

    transitions = [f for f in feats if f.index < len(states) - 1]
    n_trans = len(transitions)
    oscillation = round(
        sum(f.reversal for f in transitions) / n_trans
        if n_trans else 0.0, 6,
    )

    support_drops = [f.support_drop for f in feats]
    support_decay = round(
        max(support_drops) if support_drops else 0.0, 6,
    )

    return TrajectoryRisk(
        trajectory_id=trajectory_id,
        cliff_proximity=cliff_prox,
        confidence_variance=conf_var,
        branch_acceleration=branch_acc,
        oscillation_risk=oscillation,
        support_decay=support_decay,
    )


__all__ = ["TrajectoryRisk", "compute_risk"]
