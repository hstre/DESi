"""DESi v3.72 — Mozart predictive forecast.

Pre-activation forecast using only state[0].novelty.
Mozart's state[0].novelty = 12.0 is the strict
maximum across the 395-trajectory corpus; the
forecast asks whether that single feature is enough
to flag Mozart as a coverage outlier before any
trajectory unfolds.
"""
from __future__ import annotations

from .forecast import ForecastSummary, run_forecast
from .predict import (
    ForecastPoint, forecast_score,
    max_novelty_at_zero,
    per_trajectory_forecast, state0_novelty,
)
from .report import (
    V372Report,
    build_mozart_forecast_artifact, build_report,
)


__all__ = [
    "ForecastPoint", "ForecastSummary",
    "V372Report",
    "build_mozart_forecast_artifact",
    "build_report", "forecast_score",
    "max_novelty_at_zero",
    "per_trajectory_forecast", "run_forecast",
    "state0_novelty",
]
