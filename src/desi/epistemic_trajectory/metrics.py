"""Aufgabe 3 — per-trajectory geometric metrics."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .state import DIMENSION_NAMES, StateVector


@dataclass(frozen=True)
class TrajectoryMetrics:
    trajectory_id: str
    smoothness: float
    curvature: float
    jerk: float
    direction_reversal_rate: float
    frame_flip_rate: float
    support_state_instability: float
    manifold_departure_score: float
    transition_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "smoothness": self.smoothness,
            "curvature": self.curvature,
            "jerk": self.jerk,
            "direction_reversal_rate": self.direction_reversal_rate,
            "frame_flip_rate": self.frame_flip_rate,
            "support_state_instability": self.support_state_instability,
            "manifold_departure_score": self.manifold_departure_score,
            "transition_count": self.transition_count,
        }

    def feature_tuple(self) -> tuple[float, ...]:
        return (
            self.smoothness, self.curvature, self.jerk,
            self.direction_reversal_rate, self.frame_flip_rate,
            self.support_state_instability,
            self.manifold_departure_score,
        )


def _delta(a: StateVector, b: StateVector,
           mask: frozenset[str] | None = None) -> tuple[float, ...]:
    out: list[float] = []
    at, bt = a.to_tuple(), b.to_tuple()
    for i, name in enumerate(DIMENSION_NAMES):
        if mask is not None and name in mask:
            out.append(0.0)
        else:
            out.append(bt[i] - at[i])
    return tuple(out)


def _norm(v: tuple[float, ...]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _diff(a: tuple[float, ...],
          b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(bi - ai for ai, bi in zip(a, b))


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(ai * bi for ai, bi in zip(a, b))


def compute_metrics(
    trajectory_id: str,
    states: tuple[StateVector, ...],
    valid_centroid: tuple[float, ...] | None = None,
    *,
    mask_support_state: bool = False,
) -> TrajectoryMetrics:
    mask: frozenset[str] | None = None
    if mask_support_state:
        mask = frozenset({"support_state"})

    if len(states) < 2:
        return TrajectoryMetrics(
            trajectory_id=trajectory_id,
            smoothness=0.0, curvature=0.0, jerk=0.0,
            direction_reversal_rate=0.0, frame_flip_rate=0.0,
            support_state_instability=0.0,
            manifold_departure_score=0.0,
            transition_count=0,
        )

    deltas = [
        _delta(states[i], states[i + 1], mask=mask)
        for i in range(len(states) - 1)
    ]
    smoothness = round(sum(_norm(d) for d in deltas), 6)

    # Curvature: || Δ(t+1) - Δ(t) ||
    accelerations = [
        _diff(deltas[i], deltas[i + 1])
        for i in range(len(deltas) - 1)
    ]
    curvature = round(sum(_norm(a) for a in accelerations), 6)

    # Jerk: derivative of acceleration.
    jerks = [
        _diff(accelerations[i], accelerations[i + 1])
        for i in range(len(accelerations) - 1)
    ]
    jerk = round(sum(_norm(j) for j in jerks), 6)

    # Direction reversal: cosine between consecutive deltas
    # is negative.
    reversals = 0
    pairs = 0
    for i in range(len(deltas) - 1):
        pairs += 1
        na = _norm(deltas[i])
        nb = _norm(deltas[i + 1])
        if na == 0 or nb == 0:
            continue
        cos = _dot(deltas[i], deltas[i + 1]) / (na * nb)
        if cos < 0:
            reversals += 1
    direction_reversal_rate = (
        round(reversals / pairs, 6) if pairs else 0.0
    )

    # Frame flip rate.
    frame_idx = DIMENSION_NAMES.index("frame_id")
    flips = 0
    for i in range(len(states) - 1):
        a = states[i].to_tuple()[frame_idx]
        b = states[i + 1].to_tuple()[frame_idx]
        if a != b:
            flips += 1
    frame_flip_rate = round(flips / len(deltas), 6)

    # Support-state instability.
    sup_idx = DIMENSION_NAMES.index("support_state")
    sup_changes = sum(
        1 for i in range(len(states) - 1)
        if states[i].to_tuple()[sup_idx]
        != states[i + 1].to_tuple()[sup_idx]
    )
    support_state_instability = round(
        sup_changes / len(deltas), 6,
    )

    # Manifold departure: L2 distance of final state from
    # the supplied valid centroid.
    if valid_centroid is None:
        departure = 0.0
    else:
        final = states[-1].to_tuple()
        if mask is not None:
            final = tuple(
                0.0 if name in mask else v
                for v, name in zip(final, DIMENSION_NAMES)
            )
            valid_centroid = tuple(
                0.0 if name in mask else v
                for v, name in zip(valid_centroid, DIMENSION_NAMES)
            )
        departure = round(
            _norm(_diff(final, valid_centroid)), 6,
        )

    return TrajectoryMetrics(
        trajectory_id=trajectory_id,
        smoothness=smoothness, curvature=curvature, jerk=jerk,
        direction_reversal_rate=direction_reversal_rate,
        frame_flip_rate=frame_flip_rate,
        support_state_instability=support_state_instability,
        manifold_departure_score=departure,
        transition_count=len(deltas),
    )


def compute_centroid(
    trajectories: tuple,
) -> tuple[float, ...]:
    """Compute the centroid of FINAL states across given
    trajectories. Used as the valid manifold reference."""
    if not trajectories:
        return tuple([0.0] * len(DIMENSION_NAMES))
    dim = len(DIMENSION_NAMES)
    sums = [0.0] * dim
    n = 0
    for t in trajectories:
        if not t.states:
            continue
        final = t.states[-1].to_tuple()
        for i in range(dim):
            sums[i] += final[i]
        n += 1
    if n == 0:
        return tuple([0.0] * dim)
    return tuple(round(s / n, 6) for s in sums)


__all__ = [
    "TrajectoryMetrics",
    "compute_centroid",
    "compute_metrics",
]
