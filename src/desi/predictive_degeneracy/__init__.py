"""DESi v3.84 — predictive degeneracy probe.

Forecast pairwise doppelganger membership from
pre-coverage trajectory tail-vector distance.
Reports AUC, FPR, margin, calibration error.
"""
from __future__ import annotations

from .calibration import (
    CALIBRATION_BIN_COUNT, CalibrationBin,
    calibration_bins, calibration_error,
)
from .forecast import (
    PairForecast, all_pair_forecasts,
    false_positive_rate, forecast_margin,
    optimal_threshold, predictive_auc, roc_auc,
)
from .report import (
    CALIBRATION_ERROR_CEILING, FPR_CEILING,
    PREDICTIVE_AUC_FLOOR, V384Report,
    build_predictive_degeneracy_artifact,
    build_report,
)


__all__ = [
    "CALIBRATION_BIN_COUNT",
    "CALIBRATION_ERROR_CEILING",
    "CalibrationBin",
    "FPR_CEILING", "PREDICTIVE_AUC_FLOOR",
    "PairForecast", "V384Report",
    "all_pair_forecasts",
    "build_predictive_degeneracy_artifact",
    "build_report",
    "calibration_bins", "calibration_error",
    "false_positive_rate", "forecast_margin",
    "optimal_threshold", "predictive_auc",
    "roc_auc",
]
