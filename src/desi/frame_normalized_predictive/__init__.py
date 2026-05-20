"""DESi v3.92 — frame-normalized predictive test.

Pairwise pre-coverage forecast on the v3.89 residual
projection of the novel anchor pool. Mirrors v3.88
so the v3.85-v3.92 chain shares one methodology.
"""
from __future__ import annotations

from .forecast import (
    CALIBRATION_BIN_COUNT, CalibrationBin,
    calibration_bins, calibration_error,
    forecast_margin, frame_normalized_auc,
    frame_normalized_fpr, optimal_threshold,
    roc_auc,
)
from .predict import (
    FrameNormalizedPairForecast,
    all_normalized_pair_forecasts,
)
from .report import (
    AUC_THRESHOLD, V392Report,
    build_frame_normalized_prediction_artifact,
    build_report,
)


__all__ = [
    "AUC_THRESHOLD",
    "CALIBRATION_BIN_COUNT", "CalibrationBin",
    "FrameNormalizedPairForecast",
    "V392Report",
    "all_normalized_pair_forecasts",
    "build_frame_normalized_prediction_artifact",
    "build_report",
    "calibration_bins", "calibration_error",
    "forecast_margin", "frame_normalized_auc",
    "frame_normalized_fpr",
    "optimal_threshold", "roc_auc",
]
