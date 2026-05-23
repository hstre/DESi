"""v3.28 — per-trajectory signal extraction for root-
cause classification.

Each signal returns a numeric score in [0, ~3] derived
from existing Paper-8 state vectors and Paper-9 step
features. Higher = stronger evidence for that cause
class. No new state dimensions, no rule introspection.

Signals (one per cause class except UNKNOWN):

* support_decay        — sum of support_state drops
  across the trajectory plus a sustained-decline term.
* frame_collision      — count of frame_id flips
  weighted by accompanying delta-norm magnitude.
* branch_overload      — max(branch_cost) above a
  baseline of 3.0, plus rising branch trend.
* causal_leap          — novelty at the final state
  relative to the trajectory mean.
* confidence_osc       — variance of confidence across
  states plus alternating-sign confidence_jitter.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from ..trajectory_control.state import (
    StepFeatures, compute_step_features,
)


_IDX_FRAME      = DIMENSION_NAMES.index("frame_id")
_IDX_CONF       = DIMENSION_NAMES.index("confidence")
_IDX_BRANCH     = DIMENSION_NAMES.index("branch_cost")
_IDX_SUPPORT    = DIMENSION_NAMES.index("support_state")
_IDX_NOVELTY    = DIMENSION_NAMES.index("novelty")
_IDX_CONTRA     = DIMENSION_NAMES.index(
    "contradiction_load",
)


@dataclass(frozen=True)
class CauseSignals:
    """One score per non-UNKNOWN cause class."""

    support_decay:         float
    frame_collision:       float
    branch_overload:       float
    causal_leap:           float
    confidence_oscillation: float

    def as_dict(self) -> dict[str, float]:
        return {
            "SUPPORT_DECAY":          self.support_decay,
            "FRAME_COLLISION":        self.frame_collision,
            "BRANCH_OVERLOAD":        self.branch_overload,
            "CAUSAL_LEAP":            self.causal_leap,
            "CONFIDENCE_OSCILLATION":
                self.confidence_oscillation,
        }


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def compute_signals(
    states: tuple[StateVector, ...],
    features: tuple[StepFeatures, ...] | None = None,
) -> CauseSignals:
    feats = features if features is not None else (
        compute_step_features(states)
    )
    supp = [s.to_tuple()[_IDX_SUPPORT] for s in states]
    conf = [s.to_tuple()[_IDX_CONF] for s in states]
    branch = [s.to_tuple()[_IDX_BRANCH] for s in states]
    frame = [s.to_tuple()[_IDX_FRAME] for s in states]
    novelty = [s.to_tuple()[_IDX_NOVELTY] for s in states]

    # SUPPORT_DECAY: sum of forward drops + sustained
    # decline indicator (final support < trajectory peak)
    # + "audit-step gap" magnitude. The audit-step gap
    # captures the trajectories where the audit landed
    # on GAP_DETECTED (1) or BRIDGE_REQUIRED (2) — both
    # are explicit "support is inadequate" verdicts.
    drops = sum(f.support_drop for f in feats)
    peak = max(supp) if supp else 0.0
    sustained = max(0.0, peak - supp[-1])
    final = supp[-1] if supp else 0.0
    audit_gap = (
        max(0.0, 2.5 - final) if 0.0 < final <= 2.0
        else 0.0
    )
    support_decay = round(
        drops + 0.5 * sustained + audit_gap, 6,
    )

    # FRAME_COLLISION: integer count of frame flips
    # *after* initial declaration. The s0..s2 transition
    # where frame_id moves from 0 (undeclared) to a
    # declared value is normal pipeline behaviour and
    # is not a collision. Using a plain integer count
    # (no delta_norm weighting) keeps the score
    # cross-process stable.
    flip_score = 0
    for i in range(len(states) - 1):
        a, b = frame[i], frame[i + 1]
        if a != b and a > 0.0 and b > 0.0:
            flip_score += 1
    # "Frame undeclared at audit step" surrogate: if the
    # trajectory never declared a frame by the final
    # state, count that as one collision.
    if frame and frame[-1] == 0.0:
        flip_score += 1
    frame_collision = float(flip_score)

    # BRANCH_OVERLOAD: max branch above baseline + rising
    # trend term (final - first).
    max_branch = max(branch) if branch else 0.0
    rise = max(0.0, branch[-1] - branch[0]) if branch else 0.0
    branch_overload = round(
        max(0.0, max_branch - 3.0) + 0.4 * rise, 6,
    )

    # CAUSAL_LEAP: novelty at the final state vs the
    # mean novelty across the trajectory (final-state
    # spike above the body of the trajectory).
    if novelty:
        body = novelty[:-1] if len(novelty) > 1 else novelty
        body_mean = sum(body) / len(body)
        leap = max(0.0, novelty[-1] - body_mean)
    else:
        leap = 0.0
    causal_leap = round(leap, 6)

    # CONFIDENCE_OSCILLATION: variance of confidence,
    # sign-flip count, plus persistent-low-confidence
    # surrogate (final_conf below the trustworthy floor
    # = the frame layer never got past "tension"). A
    # frame-tension chain reaching the audit step with
    # confidence ≤ 0.4 is an oscillation that never
    # resolved upward.
    var = _variance(conf)
    sign_flips = 0
    last_dir = 0
    for i in range(len(conf) - 1):
        diff = conf[i + 1] - conf[i]
        d = 1 if diff > 0 else (-1 if diff < 0 else 0)
        if d != 0 and last_dir != 0 and d != last_dir:
            sign_flips += 1
        if d != 0:
            last_dir = d
    final_conf = conf[-1] if conf else 1.0
    low_anchor = 1.5 if final_conf <= 0.4 else 0.0
    confidence_oscillation = round(
        5.0 * var + 0.5 * sign_flips + low_anchor, 6,
    )

    return CauseSignals(
        support_decay=support_decay,
        frame_collision=frame_collision,
        branch_overload=branch_overload,
        causal_leap=causal_leap,
        confidence_oscillation=confidence_oscillation,
    )


__all__ = ["CauseSignals", "compute_signals"]
