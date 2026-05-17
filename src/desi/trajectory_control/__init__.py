"""DESi v3.25 — trajectory-control observer.

Read-only observer over the existing Paper-8
``epistemic_trajectory`` components. Predicts cliff
events from per-state geometry; does not intervene.
"""
from __future__ import annotations

from .negative_controls import NCKind, TrajectoryNC, all_ncs
from .observer import (
    StepPrediction, TrajectoryObservation,
    label_cliffs, observe, predict_trajectory,
)
from .report import (
    MAX_NC_FALSE_POSITIVE_RATE,
    MIN_TWO_STEP_WARNING_RATE, V325Report, build_report,
)
from .risk import TrajectoryRisk, compute_risk
from .state import (
    CliffKind, PredictionKind, StepFeatures,
    compute_step_features,
)


__all__ = [
    "CliffKind", "MAX_NC_FALSE_POSITIVE_RATE",
    "MIN_TWO_STEP_WARNING_RATE", "NCKind",
    "PredictionKind", "StepFeatures", "StepPrediction",
    "TrajectoryNC", "TrajectoryObservation",
    "TrajectoryRisk", "V325Report", "all_ncs",
    "build_report", "compute_risk",
    "compute_step_features", "label_cliffs", "observe",
    "predict_trajectory",
]
