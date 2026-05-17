"""v3.28 — root-cause classifier.

For each cliff-bearing trajectory we compute five
signals (one per non-UNKNOWN cause class). A signal is
*dominant* if it exceeds its class threshold; the
classifier returns the dominant signal with the highest
score. If no signal exceeds threshold, the classifier
returns UNKNOWN.

Multi-cause: a trajectory has multiple causes when
≥ 2 signals exceed threshold simultaneously.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import Trajectory
from ..trajectory_control.observer import observe
from ..trajectory_control.state import (
    CliffKind, compute_step_features,
)
from .cause import CauseClass
from .signals import CauseSignals, compute_signals


# Closed thresholds — tuned so synthetic NCs stay
# UNKNOWN, real cliff trajectories get a named cause.
_THRESHOLDS: dict[str, float] = {
    CauseClass.SUPPORT_DECAY.value:          1.5,
    CauseClass.FRAME_COLLISION.value:        1.0,
    CauseClass.BRANCH_OVERLOAD.value:        2.0,
    CauseClass.CAUSAL_LEAP.value:            1.5,
    CauseClass.CONFIDENCE_OSCILLATION.value: 1.0,
}


@dataclass(frozen=True)
class CauseAssignment:
    trajectory_id: str
    source: str
    has_cliff: bool
    primary_cause: str            # CauseClass value
    secondary_causes: tuple[str, ...]
    signals: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source,
            "has_cliff": self.has_cliff,
            "primary_cause": self.primary_cause,
            "secondary_causes": list(self.secondary_causes),
            "signals": dict(self.signals),
        }


def _dominant(
    sigs: CauseSignals,
) -> tuple[str, tuple[str, ...]]:
    scores = sigs.as_dict()
    above = [
        (name, score) for name, score in scores.items()
        if score >= _THRESHOLDS[name]
    ]
    if not above:
        return CauseClass.UNKNOWN.value, ()
    # Primary = highest score above threshold; ties
    # broken alphabetically. Scores rounded to 2 decimals
    # before comparison so cross-process float jitter
    # (driven by hash-randomised dict iteration in
    # upstream extractors) cannot flip a boundary
    # trajectory's primary cause.
    above_sorted = sorted(
        above, key=lambda kv: (-round(kv[1], 2), kv[0]),
    )
    primary = above_sorted[0][0]
    secondaries = tuple(
        name for name, _ in above_sorted[1:]
    )
    return primary, secondaries


def classify_trajectory(
    traj: Trajectory,
) -> CauseAssignment:
    obs = observe(traj)
    feats = compute_step_features(traj.states)
    sigs = compute_signals(traj.states, feats)
    has_cliff = obs.cliff_count > 0
    # No cliff -> no cause to assign. The directive
    # forbids forced classification, and synthetic NCs
    # by design have no cliff (their final support_state
    # is SUPPORTED), so any non-UNKNOWN result on them
    # would be a false-positive cause assignment.
    if not has_cliff:
        return CauseAssignment(
            trajectory_id=traj.trajectory_id,
            source=traj.source.value,
            has_cliff=False,
            primary_cause=CauseClass.UNKNOWN.value,
            secondary_causes=(),
            signals=sigs.as_dict(),
        )
    primary, secondaries = _dominant(sigs)
    return CauseAssignment(
        trajectory_id=traj.trajectory_id,
        source=traj.source.value,
        has_cliff=has_cliff,
        primary_cause=primary,
        secondary_causes=secondaries,
        signals=sigs.as_dict(),
    )


def classify_all(
    trajectories: tuple[Trajectory, ...],
) -> tuple[CauseAssignment, ...]:
    return tuple(
        classify_trajectory(t) for t in trajectories
    )


__all__ = [
    "CauseAssignment", "classify_all",
    "classify_trajectory",
]
