"""v3.25 — trajectory-control state.

Builds on the Paper-8 `epistemic_trajectory` package
(`StateVector`, `Trajectory`, `compute_metrics`). The
sprint adds no new state-vector dimensions; it derives
per-state risk features from the existing geometry.

Closed feature schema (per state index ``i`` in a
trajectory):

* ``delta_norm``         — L2 norm of state vector
  difference ``s_i → s_{i+1}``. 0 for the final state.
* ``cosine_to_prev``     — cosine of angle between
  consecutive deltas. 0 for the first / last state.
* ``support_drop``       — (s_i.support_state -
  s_{i+1}.support_state), clamped to ≥ 0.
* ``confidence_jitter``  — |s_i.confidence -
  s_{i+1}.confidence|.
* ``branch_jerk``        — 2nd derivative of
  branch_cost. 0 for boundary states.
* ``frame_flip``         — 1.0 if frame_id changes
  s_i → s_{i+1}, else 0.0.
* ``reversal``           — 1.0 if cosine_to_prev < 0.

The closed enums declare cliff kinds and observer
prediction kinds.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)


class CliffKind(str, Enum):
    """Closed taxonomy of ground-truth cliff events."""

    NONE                  = "none"
    SUPPORT_COLLAPSE      = "support_collapse"
    DIRECTION_REVERSAL    = "direction_reversal"
    LARGE_JERK            = "large_jerk"
    FRAME_FLIP_COMBO      = "frame_flip_combo"


class PredictionKind(str, Enum):
    """Closed observer-output kinds."""

    NO_CLIFF              = "no_cliff"
    CLIFF_NEXT_STEP       = "cliff_next_step"
    CLIFF_TWO_STEP        = "cliff_two_step"
    CLIFF_LATER           = "cliff_later"


# Indices into the StateVector tuple.
_IDX_FRAME      = DIMENSION_NAMES.index("frame_id")
_IDX_CONF       = DIMENSION_NAMES.index("confidence")
_IDX_BRANCH     = DIMENSION_NAMES.index("branch_cost")
_IDX_SUPPORT    = DIMENSION_NAMES.index("support_state")


@dataclass(frozen=True)
class StepFeatures:
    """Per-state-index features derived from the
    trajectory geometry. ``index`` is the state index in
    the trajectory; transitions reference index→index+1."""

    index: int
    delta_norm: float
    cosine_to_prev: float
    support_drop: float
    confidence_jitter: float
    branch_jerk: float
    frame_flip: float
    reversal: float

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "delta_norm": self.delta_norm,
            "cosine_to_prev": self.cosine_to_prev,
            "support_drop": self.support_drop,
            "confidence_jitter": self.confidence_jitter,
            "branch_jerk": self.branch_jerk,
            "frame_flip": self.frame_flip,
            "reversal": self.reversal,
        }


def _delta(a: StateVector, b: StateVector) -> tuple[float, ...]:
    return tuple(
        y - x for x, y in zip(a.to_tuple(), b.to_tuple())
    )


def _norm(v: tuple[float, ...]) -> float:
    return sum(x * x for x in v) ** 0.5


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_step_features(
    states: tuple[StateVector, ...],
) -> tuple[StepFeatures, ...]:
    """Compute per-state features for an entire
    trajectory. The last index is included but its
    transition-derived fields are 0 (no s_{i+1})."""
    out: list[StepFeatures] = []
    n = len(states)
    deltas = [
        _delta(states[i], states[i + 1])
        for i in range(n - 1)
    ]
    for i in range(n):
        if i < n - 1:
            d = deltas[i]
            delta_norm = _norm(d)
            # cosine vs previous delta
            if i > 0:
                d_prev = deltas[i - 1]
                na = _norm(d_prev)
                nb = delta_norm
                cosine = (
                    _dot(d_prev, d) / (na * nb)
                    if na > 0 and nb > 0 else 0.0
                )
            else:
                cosine = 0.0
            s_now = states[i].to_tuple()
            s_next = states[i + 1].to_tuple()
            support_drop = max(
                0.0, s_now[_IDX_SUPPORT] - s_next[_IDX_SUPPORT],
            )
            conf_jitter = abs(
                s_now[_IDX_CONF] - s_next[_IDX_CONF],
            )
            frame_flip = (
                1.0 if s_now[_IDX_FRAME] != s_next[_IDX_FRAME]
                else 0.0
            )
            # branch_jerk = 2nd derivative at index i, i.e.
            # branch[i+2] - 2*branch[i+1] + branch[i]; only
            # defined for i <= n-3.
            if i <= n - 3:
                s_2 = states[i + 2].to_tuple()
                branch_jerk = (
                    s_2[_IDX_BRANCH]
                    - 2.0 * s_next[_IDX_BRANCH]
                    + s_now[_IDX_BRANCH]
                )
            else:
                branch_jerk = 0.0
            reversal = 1.0 if cosine < 0 else 0.0
        else:
            delta_norm = 0.0
            cosine = 0.0
            support_drop = 0.0
            conf_jitter = 0.0
            branch_jerk = 0.0
            frame_flip = 0.0
            reversal = 0.0
        out.append(StepFeatures(
            index=i,
            delta_norm=round(delta_norm, 6),
            cosine_to_prev=round(cosine, 6),
            support_drop=round(support_drop, 6),
            confidence_jitter=round(conf_jitter, 6),
            branch_jerk=round(branch_jerk, 6),
            frame_flip=round(frame_flip, 6),
            reversal=round(reversal, 6),
        ))
    return tuple(out)


__all__ = [
    "CliffKind", "PredictionKind", "StepFeatures",
    "compute_step_features",
]
