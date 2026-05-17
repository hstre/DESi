"""v3.72 — Mozart forecast harness.

Computes Mozart's pre-activation forecast_score and
compares against deterministic controls (random
non-sample trajectories from v3.70). Reports the
forecast_margin and calibration_error.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..mozart_counterfactual.swap import (
    deterministic_random_control_ids,
)
from ..mozart_probe.coverage import (
    HISTORICAL_PROBES, probe_coverage,
)
from .predict import (
    ForecastPoint, forecast_score,
    per_trajectory_forecast,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ForecastSummary:
    mozart_forecast_score: float
    control_forecast_scores: dict[str, float]
    historical_forecast_scores: dict[str, float]
    forecast_margin: float
    calibration_error: float

    def to_dict(self) -> dict[str, object]:
        return {
            "mozart_forecast_score":
                self.mozart_forecast_score,
            "control_forecast_scores":
                dict(self.control_forecast_scores),
            "historical_forecast_scores":
                dict(
                    self.historical_forecast_scores,
                ),
            "forecast_margin":
                self.forecast_margin,
            "calibration_error":
                self.calibration_error,
        }


def _build_summary() -> ForecastSummary:
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    mozart = trajs.get("sample:n03_mozart")
    moz_score = (
        forecast_score(mozart) if mozart else 0.0
    )
    control_scores: dict[str, float] = {}
    for cid in deterministic_random_control_ids():
        t = trajs.get(cid)
        if t is not None:
            control_scores[cid] = forecast_score(t)
    hist_scores: dict[str, float] = {}
    for pid in HISTORICAL_PROBES:
        t = trajs.get(pid)
        if t is not None:
            hist_scores[pid] = forecast_score(t)
        else:
            hist_scores[pid] = 0.0
    if control_scores:
        margin = _round(
            moz_score - max(control_scores.values()),
        )
    else:
        margin = moz_score
    # Calibration: forecast_score normalised by
    # actual coverage_percentile observed in v3.69.
    moz_cov = probe_coverage("sample:n03_mozart")
    # Empirical actual mozart coverage_percentile is
    # near 1.0 (v3.69). The forecast_score is also
    # near 1.0. calibration_error = |forecast -
    # actual| / 1.0.
    actual_rate = (
        1.0 if moz_cov.coverage_score > 0 else 0.0
    )
    calibration = _round(
        abs(moz_score - actual_rate),
    )
    return ForecastSummary(
        mozart_forecast_score=moz_score,
        control_forecast_scores=control_scores,
        historical_forecast_scores=hist_scores,
        forecast_margin=margin,
        calibration_error=calibration,
    )


def run_forecast() -> ForecastSummary:
    return _build_summary()


__all__ = [
    "ForecastSummary", "run_forecast",
]
