"""v3.68 — pre-activation forecast harness.

A FORECAST predicts pair resonance BEFORE the v3.50
intervention is applied. The constraint: only
features available pre-activation are eligible.

* ``distance``       — Euclidean over the static
  trajectory vectors; computable before any
  intervention.
* ``heterogeneity``  — corpus prefix; static.
* ``diversity``      — failure profile (cause /
  source / final-state pattern); static.

``coverage_gain`` is EXCLUDED from the forecast model
because computing it requires having observed the
post-activation coverage sets. The directive's
"Vorhersage vor Aktivierung" rules it out.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..predictive.blind_split import (
    test_pairs, train_pairs,
)
from ..predictive.predictor import (
    EvaluationResult, evaluate, fit,
)


PRE_ACTIVATION_FEATURES: tuple[str, ...] = (
    "distance", "heterogeneity", "diversity",
)
"""Closed feature set available before the v3.50
intervention fires (excludes coverage_gain)."""

EARLY_WARNING_STEPS: int = 4
"""Number of pre-audit trajectory states. For every
plateau trajectory in the v3.50 universe the audit
fires at state index n-1 = 4; the forecast is
available at state index 0, so the early-warning
horizon is 4 steps."""


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ForecastResult:
    evaluation: EvaluationResult
    forecast_accuracy: float
    calibration_error: float
    predicted_positives: int
    actual_positives: int
    early_warning_steps: int

    def to_dict(self) -> dict[str, object]:
        return {
            "evaluation":
                self.evaluation.to_dict(),
            "forecast_accuracy":
                self.forecast_accuracy,
            "calibration_error":
                self.calibration_error,
            "predicted_positives":
                self.predicted_positives,
            "actual_positives":
                self.actual_positives,
            "early_warning_steps":
                self.early_warning_steps,
        }


def run_forecast() -> ForecastResult:
    model = fit(
        train_pairs(),
        feature_names=PRE_ACTIVATION_FEATURES,
    )
    test = test_pairs()
    result = evaluate(model, test)
    total = len(test)
    tp = result.true_positive_count
    tn = result.true_negative_count
    fp = result.false_positive_count
    fn = result.false_negative_count
    accuracy = _round(
        (tp + tn) / total if total else 0.0,
    )
    predicted_pos = tp + fp
    actual_pos = tp + fn
    calibration = _round(
        abs(predicted_pos - actual_pos) / total
        if total else 0.0,
    )
    return ForecastResult(
        evaluation=result,
        forecast_accuracy=accuracy,
        calibration_error=calibration,
        predicted_positives=predicted_pos,
        actual_positives=actual_pos,
        early_warning_steps=EARLY_WARNING_STEPS,
    )


def trained_forecast_model():
    return fit(
        train_pairs(),
        feature_names=PRE_ACTIVATION_FEATURES,
    )


__all__ = [
    "EARLY_WARNING_STEPS", "ForecastResult",
    "PRE_ACTIVATION_FEATURES", "run_forecast",
    "trained_forecast_model",
]
