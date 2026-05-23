"""DESi v3.124 — full-regression validation."""
from __future__ import annotations

from .validation import (
    HashCheck, V3124FullRegressionReport,
    adverse_flip_count,
    build_full_regression_validation_artifact,
    build_report, full_regression_passed,
    full_regression_status, hash_checks,
    hash_stability, historical_far,
    historical_tpr, matrix_drift_count,
    matrix_drift_entries, rule_roi,
    v2_8_failcase_live_hash,
    v2_8_reconstruction_live_hash,
)


__all__ = [
    "HashCheck",
    "V3124FullRegressionReport",
    "adverse_flip_count",
    "build_full_regression_validation_artifact",
    "build_report",
    "full_regression_passed",
    "full_regression_status",
    "hash_checks",
    "hash_stability",
    "historical_far",
    "historical_tpr",
    "matrix_drift_count",
    "matrix_drift_entries",
    "rule_roi",
    "v2_8_failcase_live_hash",
    "v2_8_reconstruction_live_hash",
]
