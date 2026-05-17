"""DESi trajectory-control sprint (v3.25 / v3.26).

v3.25 — observer: cliff prediction, no intervention.
v3.26 — passive controller: closed action set
        (branch_freeze / forced_replay / confidence_hold);
        no rule changes, no frame overrides, no causal
        overrides; counterfactual trajectories only.
"""
from __future__ import annotations

from .actions import (
    ActionKind, AppliedAction, apply_action,
    apply_branch_freeze, apply_confidence_hold,
    apply_forced_replay,
)
from .controller import (
    ControllerOutcome, control_all, control_trajectory,
)
from .negative_controls import NCKind, TrajectoryNC, all_ncs
from .observer import (
    StepPrediction, TrajectoryObservation,
    label_cliffs, observe, predict_trajectory,
)
from .policies import PolicyDecision, decide
from .report import (
    MAX_NC_FALSE_POSITIVE_RATE,
    MIN_TWO_STEP_WARNING_RATE, V325Report, build_report,
)
from .report_v3_26 import (
    MAX_FALSE_INTERVENTION_RATE,
    MAX_NC_INTERVENTION_RATE, V326Report,
    build_report as build_v3_26_report,
)
from .risk import TrajectoryRisk, compute_risk
from .state import (
    CliffKind, PredictionKind, StepFeatures,
    compute_step_features,
)


__all__ = [
    "ActionKind", "AppliedAction", "CliffKind",
    "ControllerOutcome",
    "MAX_FALSE_INTERVENTION_RATE",
    "MAX_NC_FALSE_POSITIVE_RATE",
    "MAX_NC_INTERVENTION_RATE",
    "MIN_TWO_STEP_WARNING_RATE",
    "NCKind", "PolicyDecision", "PredictionKind",
    "StepFeatures", "StepPrediction", "TrajectoryNC",
    "TrajectoryObservation", "TrajectoryRisk",
    "V325Report", "V326Report",
    "all_ncs", "apply_action",
    "apply_branch_freeze", "apply_confidence_hold",
    "apply_forced_replay", "build_report",
    "build_v3_26_report", "compute_risk",
    "compute_step_features", "control_all",
    "control_trajectory", "decide",
    "label_cliffs", "observe", "predict_trajectory",
]
