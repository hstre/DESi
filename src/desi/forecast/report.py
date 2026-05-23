"""v3.68 — causal forecast report.

Pflichtmetriken (directive § v3.68):

* ``forecast_accuracy``
* ``calibration_error``
* ``early_warning_steps``
* ``forecast_replay_stability``

Paper-11 final gate #5:
``forecast_accuracy >= 0.70``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .forecast import (
    EARLY_WARNING_STEPS, PRE_ACTIVATION_FEATURES,
    run_forecast, trained_forecast_model,
)


FORECAST_ACCURACY_FLOOR: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V368Report:
    pre_activation_features: tuple[str, ...]
    model: dict
    forecast: dict
    forecast_accuracy: float
    calibration_error: float
    early_warning_steps: int
    forecast_replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pre_activation_features":
                list(self.pre_activation_features),
            "model": self.model,
            "forecast": self.forecast,
            "forecast_accuracy":
                self.forecast_accuracy,
            "calibration_error":
                self.calibration_error,
            "early_warning_steps":
                self.early_warning_steps,
            "forecast_replay_stability":
                self.forecast_replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = trained_forecast_model().to_dict()
    b = trained_forecast_model().to_dict()
    if a == b:
        return 1.0
    return 0.0


def build_report() -> V368Report:
    forecast = run_forecast()
    model = trained_forecast_model()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif forecast.forecast_accuracy >= (
        FORECAST_ACCURACY_FLOOR
    ):
        verdict = "FORECAST_USABLE"
    else:
        verdict = "FORECAST_BELOW_FLOOR"

    rationale = (
        f"INFO: pre_activation_features "
        f"{list(PRE_ACTIVATION_FEATURES)}",
        f"INFO: model weights {model.weights}, "
        f"threshold {model.threshold}",
        f"INFO: forecast {forecast.to_dict()}",
        f"{'PASS' if forecast.forecast_accuracy >= FORECAST_ACCURACY_FLOOR else 'FAIL'}: "
        f"forecast_accuracy "
        f"{forecast.forecast_accuracy} >= "
        f"{FORECAST_ACCURACY_FLOOR}",
        f"INFO: early_warning_steps "
        f"{forecast.early_warning_steps}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"forecast_replay_stability {replay}",
    )

    return V368Report(
        pre_activation_features=(
            PRE_ACTIVATION_FEATURES
        ),
        model=model.to_dict(),
        forecast=forecast.to_dict(),
        forecast_accuracy=(
            forecast.forecast_accuracy
        ),
        calibration_error=(
            forecast.calibration_error
        ),
        early_warning_steps=EARLY_WARNING_STEPS,
        forecast_replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_activation_forecast_artifact(
) -> dict[str, object]:
    forecast = run_forecast()
    model = trained_forecast_model()
    return {
        "schema_version":
            "v3_68_activation_forecast",
        "pre_activation_features":
            list(PRE_ACTIVATION_FEATURES),
        "model": model.to_dict(),
        "forecast": forecast.to_dict(),
    }


__all__ = [
    "FORECAST_ACCURACY_FLOOR", "V368Report",
    "build_activation_forecast_artifact",
    "build_report",
]
