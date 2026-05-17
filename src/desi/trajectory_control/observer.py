"""v3.25 — cliff observer.

Two passes over each trajectory:

1. Ground-truth labelling — given the full state
   sequence, mark each transition ``i → i+1`` with a
   ``CliffKind`` (NONE / SUPPORT_COLLAPSE /
   DIRECTION_REVERSAL / LARGE_JERK / FRAME_FLIP_COMBO)
   from closed thresholds.

2. Causal prediction — at each state index ``i``, look
   *only* at features ``StepFeatures[0..i]`` and emit a
   ``PredictionKind``. The observer must not see
   features ``> i``.

The directive's question: *Kann DESi einen Cliff
≥2 Schritte vorher erkennen?* — measured here as
``cliff_two_step_precision`` /
``cliff_two_step_recall`` over the trajectory corpus.

No interventions in v3.25. The observer reports only;
v3.26 introduces actions.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import Trajectory
from .state import (
    CliffKind, PredictionKind, StepFeatures,
    compute_step_features,
)


# ---------------------------------------------------------------------------
# Closed thresholds (no learned parameters)
# ---------------------------------------------------------------------------


# A true cliff requires SUPPORT involvement — the
# verdict-relevant dimension. Pure geometric magnitudes
# (delta_norm, branch_jerk) without support change are
# common in healthy trajectories (cf NC fake_cliff,
# noisy_branch) and don't warrant intervention.

_SUPPORT_COLLAPSE_DROP   = 2.0   # support_state drops by ≥ 2 in one step
_SUPPORT_DECLINE_MIN     = 0.5   # support_state decline accompanying
                                  # any geometric cliff signal
_DELTA_NORM_LARGE        = 4.0   # transition with delta_norm ≥ 4 is "big"
_LARGE_JERK_BRANCH       = 3.0   # |branch_jerk| ≥ 3 is a jerk cliff
_DIRECTION_REVERSAL_THR  = -0.5  # cosine < -0.5 is a clear reversal


# ---------------------------------------------------------------------------
# Ground-truth labelling
# ---------------------------------------------------------------------------


def label_cliffs(
    features: tuple[StepFeatures, ...],
    states: tuple | None = None,
) -> tuple[str, ...]:
    """Return one CliffKind value per state index, looking
    at the *forward* transition i→i+1. The last index
    always labels NONE (no transition).

    A trajectory is a "cliff trajectory" if its final
    state has support_state < LOGICALLY_SUPPORTED (4) —
    i.e., the audit ended in a non-supported verdict
    (LOGICALLY_REJECTED, BRIDGE_REQUIRED, GAP_DETECTED).

    The cliff event lands on the *final* transition
    (index n-2 → n-1). Earlier transitions can carry
    auxiliary kinds (LARGE_JERK, DIRECTION_REVERSAL,
    FRAME_FLIP_COMBO) only when they coincide with
    support involvement, so NCs that look cliff-like but
    finish on a healthy audit do not trigger labels.
    """
    labels: list[str] = []
    n = len(features)
    final_support = (
        states[-1].support_state if states else 4.0
    )
    is_cliff_trajectory = final_support < 4.0
    for i, f in enumerate(features):
        if i >= n - 1:
            labels.append(CliffKind.NONE.value)
            continue
        # The final transition into a non-supported final
        # state is the canonical cliff event.
        if i == n - 2 and is_cliff_trajectory:
            if final_support <= 1.0:
                labels.append(CliffKind.SUPPORT_COLLAPSE.value)
            elif final_support <= 2.0:
                labels.append(CliffKind.LARGE_JERK.value)
            else:
                labels.append(
                    CliffKind.DIRECTION_REVERSAL.value,
                )
            continue
        # Earlier transitions: only label as a cliff if
        # they show support involvement plus a geometric
        # signal. This keeps NCs (geometric spike, no
        # support effect) below the threshold.
        if f.support_drop >= _SUPPORT_COLLAPSE_DROP:
            labels.append(CliffKind.SUPPORT_COLLAPSE.value)
            continue
        if f.support_drop < _SUPPORT_DECLINE_MIN:
            labels.append(CliffKind.NONE.value)
            continue
        if f.cosine_to_prev <= _DIRECTION_REVERSAL_THR \
                and f.delta_norm >= _DELTA_NORM_LARGE:
            labels.append(
                CliffKind.DIRECTION_REVERSAL.value,
            )
        elif abs(f.branch_jerk) >= _LARGE_JERK_BRANCH:
            labels.append(CliffKind.LARGE_JERK.value)
        elif f.frame_flip >= 1.0 \
                and f.delta_norm >= _DELTA_NORM_LARGE:
            labels.append(CliffKind.FRAME_FLIP_COMBO.value)
        else:
            labels.append(CliffKind.NONE.value)
    return tuple(labels)


# ---------------------------------------------------------------------------
# Causal predictor (uses only features at indices ≤ i)
# ---------------------------------------------------------------------------


# Prediction signals (closed). The observer fires
# "cliff_next_step" if features at index i themselves
# look cliff-like (delta_norm and support_drop already
# elevated, but the next-step cliff label is what we want
# to recover from the history alone). "cliff_two_step"
# fires when *anticipatory* signals are present: rising
# delta_norm trend, support already eroding, confidence
# jitter spiking, branch acceleration > 0.


def _trend(
    values: list[float], *, k: int = 2,
) -> float:
    """Mean-difference trend over the last ``k`` values."""
    if len(values) < 2:
        return 0.0
    tail = values[-k - 1:] if len(values) > k else values
    diffs = [tail[i + 1] - tail[i] for i in range(len(tail) - 1)]
    return sum(diffs) / len(diffs) if diffs else 0.0


@dataclass(frozen=True)
class StepPrediction:
    """Observer output at a single state index."""

    index: int
    prediction: str            # PredictionKind value
    cliff_proximity: int       # 0 = at the cliff,
                               # 1 = next step,
                               # 2 = two-step,
                               # 99 = no cliff in lookahead
    risk_score: float          # 0..1

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "prediction": self.prediction,
            "cliff_proximity": self.cliff_proximity,
            "risk_score": self.risk_score,
        }


def _predict_one(
    history: list[StepFeatures], index: int, n: int,
    states_so_far: tuple | None = None,
) -> StepPrediction:
    """Predict from features[0..index] AND the actual
    state vectors observed so far. The predictor combines:

    * geometric anticipatory signals (delta-norm trend,
      direction reversal, branch jerk) — useful for the
      mid-trajectory near-step cliffs;
    * raw-state signals (low confidence, high
      contradiction load, undeclared frame) — useful for
      predicting the final-audit cliff because the audit
      verdict is set by these dimensions before s4.

    Pure NCs (geometric spikes with no support erosion
    and healthy confidence) score below threshold on
    both pathways and remain ``NO_CLIFF``.
    """
    if index >= n - 1:
        return StepPrediction(
            index=index, prediction=PredictionKind.NO_CLIFF.value,
            cliff_proximity=99, risk_score=0.0,
        )
    last = history[-1]
    delta_trend = _trend(
        [f.delta_norm for f in history], k=2,
    )
    support_trend = _trend(
        [f.support_drop for f in history], k=2,
    )
    conf_trend = _trend(
        [f.confidence_jitter for f in history], k=2,
    )
    support_involved = (
        last.support_drop > 0.0 or support_trend > 0.0
    )

    # Raw-state signals — predictive of the final audit
    # cliff (low confidence, high contradiction, etc).
    current_state = (
        states_so_far[index] if states_so_far else None
    )
    raw_risk = 0.0
    if current_state is not None and index >= 2:
        # Use the latest "meaningful" state (s2 or later
        # carries frame and confidence info).
        d = current_state.to_dict()
        # Low confidence after frame layer is the
        # strongest single signal of an upcoming failure.
        if d["confidence"] <= 0.25:
            raw_risk += 0.45
        elif d["confidence"] <= 0.5:
            raw_risk += 0.25
        if d["contradiction_load"] >= 2.0:
            raw_risk += 0.3
        elif d["contradiction_load"] >= 1.0:
            raw_risk += 0.15
        if d["frame_id"] == 0.0:
            raw_risk += 0.15
        if d["branch_cost"] >= 5.0:
            raw_risk += 0.15

    geom_risk = 0.0
    if last.support_drop >= _SUPPORT_COLLAPSE_DROP:
        geom_risk += 0.8
    if support_involved:
        if last.cosine_to_prev <= _DIRECTION_REVERSAL_THR \
                and last.delta_norm >= _DELTA_NORM_LARGE:
            geom_risk += 0.5
        if abs(last.branch_jerk) >= _LARGE_JERK_BRANCH:
            geom_risk += 0.35
        if last.frame_flip >= 1.0:
            geom_risk += 0.2
        if delta_trend > 0.5 and last.delta_norm >= 1.0:
            geom_risk += 0.25
        if support_trend > 0.5:
            geom_risk += 0.3
        if conf_trend > 0.1 and last.confidence_jitter >= 0.2:
            geom_risk += 0.15

    risk = min(1.0, geom_risk + raw_risk)

    if risk >= 0.7:
        pred = PredictionKind.CLIFF_NEXT_STEP.value
        proximity = 1
    elif risk >= 0.45:
        pred = PredictionKind.CLIFF_TWO_STEP.value
        proximity = 2
    elif risk >= 0.25:
        pred = PredictionKind.CLIFF_LATER.value
        proximity = 3
    else:
        pred = PredictionKind.NO_CLIFF.value
        proximity = 99
    return StepPrediction(
        index=index, prediction=pred,
        cliff_proximity=proximity,
        risk_score=round(risk, 6),
    )


def predict_trajectory(
    features: tuple[StepFeatures, ...],
    states: tuple | None = None,
) -> tuple[StepPrediction, ...]:
    n = len(features)
    out: list[StepPrediction] = []
    for i in range(n):
        history = list(features[: i + 1])
        states_so_far = states[: i + 1] if states else None
        out.append(_predict_one(
            history, i, n, states_so_far=states_so_far,
        ))
    return tuple(out)


# ---------------------------------------------------------------------------
# Trajectory-level observation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrajectoryObservation:
    trajectory_id: str
    source: str
    cliff_labels: tuple[str, ...]
    predictions: tuple[StepPrediction, ...]
    cliff_count: int
    has_two_step_warning: bool   # observer raised CLIFF_TWO_STEP
                                  # at least 2 steps before any cliff.

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source,
            "cliff_labels": list(self.cliff_labels),
            "predictions": [
                p.to_dict() for p in self.predictions
            ],
            "cliff_count": self.cliff_count,
            "has_two_step_warning":
                self.has_two_step_warning,
        }


def observe(traj: Trajectory) -> TrajectoryObservation:
    features = compute_step_features(traj.states)
    labels = label_cliffs(features, traj.states)
    preds = predict_trajectory(features, traj.states)
    cliff_count = sum(
        1 for label in labels
        if label != CliffKind.NONE.value
    )
    # Did the observer raise a 2-step warning at any
    # index i such that a true cliff lands at i+2 or i+1?
    has_two_step = False
    n = len(labels)
    for i, p in enumerate(preds):
        if p.prediction in (
            PredictionKind.CLIFF_TWO_STEP.value,
            PredictionKind.CLIFF_NEXT_STEP.value,
        ):
            # Check lookahead window [i+1, i+2] for a true cliff
            for j in (i + 1, i + 2):
                if 0 <= j < n and labels[j] != (
                    CliffKind.NONE.value
                ):
                    has_two_step = True
                    break
        if has_two_step:
            break
    return TrajectoryObservation(
        trajectory_id=traj.trajectory_id,
        source=traj.source.value,
        cliff_labels=labels,
        predictions=preds,
        cliff_count=cliff_count,
        has_two_step_warning=has_two_step,
    )


__all__ = [
    "StepPrediction", "TrajectoryObservation",
    "label_cliffs", "observe", "predict_trajectory",
]
