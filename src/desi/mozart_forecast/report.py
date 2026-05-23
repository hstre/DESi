"""v3.72 — Mozart forecast report.

Pflichtmetriken (directive § v3.72):

* ``mozart_forecast_score``
* ``control_forecast_scores``
* ``forecast_margin``
* ``calibration_error``
* ``replay_stability``

Paper-11 historical gate #4: ``forecast_margin > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .forecast import ForecastSummary, run_forecast
from .predict import max_novelty_at_zero


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V372Report:
    max_novelty_at_zero: float
    mozart_forecast_score: float
    control_forecast_scores: dict[str, float]
    historical_forecast_scores: dict[str, float]
    forecast_margin: float
    calibration_error: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "max_novelty_at_zero":
                self.max_novelty_at_zero,
            "mozart_forecast_score":
                self.mozart_forecast_score,
            "control_forecast_scores":
                dict(
                    self.control_forecast_scores,
                ),
            "historical_forecast_scores":
                dict(
                    self.historical_forecast_scores,
                ),
            "forecast_margin":
                self.forecast_margin,
            "calibration_error":
                self.calibration_error,
            "replay_stability":
                self.replay_stability,
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
    a = run_forecast().to_dict()
    b = run_forecast().to_dict()
    if a == b:
        return 1.0
    return 0.0


def build_report() -> V372Report:
    summary = run_forecast()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif summary.forecast_margin > 0:
        verdict = "MOZART_FORECASTABLE"
    elif summary.forecast_margin == 0:
        verdict = "MOZART_FORECAST_TIED"
    else:
        verdict = "MOZART_NOT_FORECASTABLE"

    rationale = (
        f"INFO: max_novelty_at_zero "
        f"{max_novelty_at_zero()}",
        f"INFO: mozart_forecast_score "
        f"{summary.mozart_forecast_score}",
        f"INFO: control_forecast_scores "
        f"{sorted(summary.control_forecast_scores.items())}",
        f"INFO: historical_forecast_scores "
        f"{sorted(summary.historical_forecast_scores.items())}",
        f"{'PASS' if summary.forecast_margin > 0 else 'FAIL'}: "
        f"forecast_margin "
        f"{summary.forecast_margin} > 0",
        f"INFO: calibration_error "
        f"{summary.calibration_error}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V372Report(
        max_novelty_at_zero=max_novelty_at_zero(),
        mozart_forecast_score=(
            summary.mozart_forecast_score
        ),
        control_forecast_scores=(
            summary.control_forecast_scores
        ),
        historical_forecast_scores=(
            summary.historical_forecast_scores
        ),
        forecast_margin=summary.forecast_margin,
        calibration_error=(
            summary.calibration_error
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_mozart_forecast_artifact(
) -> dict[str, object]:
    summary = run_forecast()
    return {
        "schema_version":
            "v3_72_mozart_forecast",
        "max_novelty_at_zero":
            max_novelty_at_zero(),
        "summary": summary.to_dict(),
    }


__all__ = [
    "V372Report",
    "build_mozart_forecast_artifact", "build_report",
]
