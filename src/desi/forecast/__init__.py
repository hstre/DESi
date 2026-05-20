"""DESi v3.68 — causal forecast.

Pre-activation forecast of pair resonance using only
features available BEFORE the v3.50 intervention
fires (distance, heterogeneity, diversity).
coverage_gain is excluded as a post-activation
quantity.
"""
from __future__ import annotations

from .forecast import (
    EARLY_WARNING_STEPS, ForecastResult,
    PRE_ACTIVATION_FEATURES, run_forecast,
    trained_forecast_model,
)
from .report import (
    FORECAST_ACCURACY_FLOOR, V368Report,
    build_activation_forecast_artifact, build_report,
)


__all__ = [
    "EARLY_WARNING_STEPS",
    "FORECAST_ACCURACY_FLOOR", "ForecastResult",
    "PRE_ACTIVATION_FEATURES", "V368Report",
    "build_activation_forecast_artifact",
    "build_report", "run_forecast",
    "trained_forecast_model",
]
