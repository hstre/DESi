"""DESi trajectory-control sprint (v3.25 / v3.26 / v3.27).

v3.25 — observer: cliff prediction, no intervention.
v3.26 — passive controller: closed action set
        (branch_freeze / forced_replay / confidence_hold);
        no rule changes, no frame overrides, no causal
        overrides; counterfactual trajectories only.
v3.27 — rollback action: rollback_last_transition adds
        the only action that can change the final-state
        verdict; trace log + replay-stability check.
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
from .replay_control import (
    RollbackOutcome, control_all_with_rollback,
    control_with_rollback, replay_stability,
)
from .report import (
    MAX_NC_FALSE_POSITIVE_RATE,
    MIN_TWO_STEP_WARNING_RATE, V325Report, build_report,
)
from .report_v3_26 import (
    MAX_FALSE_INTERVENTION_RATE,
    MAX_NC_INTERVENTION_RATE, V326Report,
    build_report as build_v3_26_report,
)
from .report_v3_27 import (
    MAX_NC_ROLLBACK_RATE, MAX_OVERCONTROL_RATE,
    MIN_REPLAY_STABILITY, V327Report,
    build_report as build_v3_27_report,
)
from .risk import TrajectoryRisk, compute_risk
from .rollback import (
    RollbackKind, apply_rollback_last_transition,
)
from .state import (
    CliffKind, PredictionKind, StepFeatures,
    compute_step_features,
)
from .trace import TraceEntry, TraceLog


__all__ = [
    "ActionKind", "AppliedAction", "CliffKind",
    "ControllerOutcome",
    "MAX_FALSE_INTERVENTION_RATE",
    "MAX_NC_FALSE_POSITIVE_RATE",
    "MAX_NC_INTERVENTION_RATE",
    "MAX_NC_ROLLBACK_RATE", "MAX_OVERCONTROL_RATE",
    "MIN_REPLAY_STABILITY",
    "MIN_TWO_STEP_WARNING_RATE",
    "NCKind", "PolicyDecision", "PredictionKind",
    "RollbackKind", "RollbackOutcome",
    "StepFeatures", "StepPrediction", "TraceEntry",
    "TraceLog", "TrajectoryNC",
    "TrajectoryObservation", "TrajectoryRisk",
    "V325Report", "V326Report", "V327Report",
    "all_ncs", "apply_action",
    "apply_branch_freeze", "apply_confidence_hold",
    "apply_forced_replay",
    "apply_rollback_last_transition",
    "build_report",
    "build_v3_26_report", "build_v3_27_report",
    "compute_risk", "compute_step_features",
    "control_all", "control_all_with_rollback",
    "control_trajectory", "control_with_rollback",
    "decide", "label_cliffs", "observe",
    "predict_trajectory", "replay_stability",
]
