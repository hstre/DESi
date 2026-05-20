"""DESi v3.88 — predictive novel degeneracy probe.

Pairwise pre-coverage forecast on the v3.85 novel
anchors. Score = ``-euclidean(tail_a, tail_b)``,
label = ``same_family``. ROC AUC, false positive
rate at optimum, forecast margin, and expected
calibration error follow the v3.84 template.
"""
from __future__ import annotations

from .forecast import (
    CALIBRATION_BIN_COUNT, CalibrationBin,
    calibration_bins, calibration_error,
    false_positive_rate, forecast_margin,
    optimal_threshold, predictive_auc, roc_auc,
)
from .predict import (
    NovelPairForecast, all_novel_pair_forecasts,
)
from .report import (
    AUC_THRESHOLD, V388Report,
    build_novel_family_predictive_artifact,
    build_report,
)


__all__ = [
    "AUC_THRESHOLD",
    "CALIBRATION_BIN_COUNT", "CalibrationBin",
    "NovelPairForecast",
    "V388Report",
    "all_novel_pair_forecasts",
    "build_novel_family_predictive_artifact",
    "build_report",
    "calibration_bins", "calibration_error",
    "false_positive_rate", "forecast_margin",
    "optimal_threshold", "predictive_auc",
    "roc_auc",
]
