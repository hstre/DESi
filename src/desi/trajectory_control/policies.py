"""v3.26 — closed action-selection policy.

Given an observer's per-state predictions plus the
trajectory state vectors, the policy returns an
``ActionKind`` if intervention is warranted (else
``None``). The policy is a closed deterministic
cascade — no learned weights.

Selection rules (in order):

1. If the latest state's contradiction_load >= 1.0 and
   confidence ≤ 0.5 ⇒ ``confidence_hold``.
2. If the predictor sees a rising branch-cost trend and
   the current branch_cost > 4.0 ⇒ ``branch_freeze``.
3. If the latest state's frame_id == 0.0 (undeclared)
   AND the predictor warns within 1-2 steps ⇒
   ``forced_replay``.
4. Else if predictor predicts CLIFF_NEXT_STEP ⇒
   ``confidence_hold`` (safest default).
5. Else ⇒ no action.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..epistemic_trajectory.state import StateVector
from .actions import ActionKind
from .observer import StepPrediction
from .state import PredictionKind, StepFeatures


@dataclass(frozen=True)
class PolicyDecision:
    """Per-state-index decision."""

    index: int
    action: Optional[str]   # ActionKind value or None
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "action": self.action,
            "rationale": self.rationale,
        }


_WARNING_KINDS = {
    PredictionKind.CLIFF_NEXT_STEP.value,
    PredictionKind.CLIFF_TWO_STEP.value,
}


def decide(
    state: StateVector, feature: StepFeatures,
    prediction: StepPrediction,
    branch_history: list[float],
) -> PolicyDecision:
    if prediction.prediction not in _WARNING_KINDS:
        return PolicyDecision(
            index=prediction.index, action=None,
            rationale="no_warning",
        )
    # Rule 1: contradiction + low confidence
    if state.contradiction_load >= 1.0 and \
            state.confidence <= 0.5:
        return PolicyDecision(
            index=prediction.index,
            action=ActionKind.CONFIDENCE_HOLD.value,
            rationale="contradiction_with_low_confidence",
        )
    # Rule 2: rising branch trend + high branch
    if len(branch_history) >= 2:
        trend = branch_history[-1] - branch_history[-2]
    else:
        trend = 0.0
    if trend > 0.5 and state.branch_cost > 4.0:
        return PolicyDecision(
            index=prediction.index,
            action=ActionKind.BRANCH_FREEZE.value,
            rationale="branch_growth_above_threshold",
        )
    # Rule 3: undeclared frame + warning
    if state.frame_id == 0.0 and \
            prediction.prediction == (
                PredictionKind.CLIFF_NEXT_STEP.value
            ):
        return PolicyDecision(
            index=prediction.index,
            action=ActionKind.FORCED_REPLAY.value,
            rationale="undeclared_frame_with_warning",
        )
    # Rule 4: any next-step warning ⇒ safest default
    if prediction.prediction == (
        PredictionKind.CLIFF_NEXT_STEP.value
    ):
        return PolicyDecision(
            index=prediction.index,
            action=ActionKind.CONFIDENCE_HOLD.value,
            rationale="next_step_warning_default",
        )
    return PolicyDecision(
        index=prediction.index, action=None,
        rationale="two_step_warning_holds",
    )


__all__ = ["PolicyDecision", "decide"]
