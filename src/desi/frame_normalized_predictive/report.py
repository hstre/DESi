"""v3.92 — frame-normalized predictive test report.

Pflichtmetriken (directive § v3.92):

* ``frame_normalized_auc``
* ``frame_normalized_fpr``
* ``forecast_margin``
* ``calibration_error``
* ``replay_stability``

Concept Gate condition #4: ``frame_normalized_auc
>= 0.70``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..novel_predictive.forecast import (
    predictive_auc as raw_predictive_auc,
)
from .forecast import (
    calibration_bins, calibration_error,
    forecast_margin, frame_normalized_auc,
    frame_normalized_fpr, optimal_threshold,
)
from .predict import (
    all_normalized_pair_forecasts,
)


AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V392Report:
    pair_count: int
    same_family_pair_count: int
    cross_family_pair_count: int
    raw_predictive_auc: float
    frame_normalized_auc: float
    auc_delta: float
    forecast_margin: float
    optimal_threshold: float
    frame_normalized_fpr: float
    calibration_error: float
    calibration_bins: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pair_count": self.pair_count,
            "same_family_pair_count":
                self.same_family_pair_count,
            "cross_family_pair_count":
                self.cross_family_pair_count,
            "raw_predictive_auc":
                self.raw_predictive_auc,
            "frame_normalized_auc":
                self.frame_normalized_auc,
            "auc_delta": self.auc_delta,
            "forecast_margin":
                self.forecast_margin,
            "optimal_threshold":
                self.optimal_threshold,
            "frame_normalized_fpr":
                self.frame_normalized_fpr,
            "calibration_error":
                self.calibration_error,
            "calibration_bins":
                list(self.calibration_bins),
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
    a = (
        frame_normalized_auc(),
        forecast_margin(),
        optimal_threshold(),
        calibration_error(),
    )
    b = (
        frame_normalized_auc(),
        forecast_margin(),
        optimal_threshold(),
        calibration_error(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V392Report:
    pairs = all_normalized_pair_forecasts()
    pos = sum(1 for p in pairs if p.same_family)
    neg = sum(1 for p in pairs if not p.same_family)
    raw_auc = raw_predictive_auc()
    auc = frame_normalized_auc()
    delta = _round(auc - raw_auc)
    margin = forecast_margin()
    thr = optimal_threshold()
    fpr = frame_normalized_fpr(thr)
    cerr = calibration_error()
    bins = calibration_bins()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif auc >= AUC_THRESHOLD:
        verdict = (
            "FRAME_NORMALIZED_DEGENERACY_PREDICTABLE"
        )
    elif auc > raw_auc:
        verdict = (
            "FRAME_NORMALIZED_DEGENERACY_WEAK_GAIN"
        )
    else:
        verdict = (
            "FRAME_NORMALIZED_DEGENERACY_NO_GAIN"
        )

    rationale = (
        f"INFO: pair_count {len(pairs)} "
        f"(positives={pos}, negatives={neg})",
        f"INFO: raw_predictive_auc {raw_auc} "
        f"(v3.88 baseline)",
        f"{'PASS' if auc >= AUC_THRESHOLD else 'FAIL'}: "
        f"frame_normalized_auc {auc} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: auc_delta {delta} "
        f"(normalized minus raw)",
        f"INFO: forecast_margin {margin} "
        f"(positive ⇒ fully separable)",
        f"INFO: optimal_threshold {thr}",
        f"INFO: frame_normalized_fpr {fpr}",
        f"INFO: calibration_error {cerr}",
        f"INFO: calibration_bins "
        f"{[b.to_dict() for b in bins]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V392Report(
        pair_count=len(pairs),
        same_family_pair_count=pos,
        cross_family_pair_count=neg,
        raw_predictive_auc=raw_auc,
        frame_normalized_auc=auc,
        auc_delta=delta,
        forecast_margin=margin,
        optimal_threshold=thr,
        frame_normalized_fpr=fpr,
        calibration_error=cerr,
        calibration_bins=tuple(
            b.to_dict() for b in bins
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_frame_normalized_prediction_artifact(
) -> dict[str, object]:
    pairs = all_normalized_pair_forecasts()
    return {
        "schema_version":
            "v3_92_frame_normalized_prediction",
        "pair_count": len(pairs),
        "frame_normalized_auc":
            frame_normalized_auc(),
        "forecast_margin": forecast_margin(),
        "optimal_threshold":
            optimal_threshold(),
        "frame_normalized_fpr":
            frame_normalized_fpr(
                optimal_threshold(),
            ),
        "calibration_error":
            calibration_error(),
        "pair_forecasts": [
            p.to_dict() for p in pairs
        ],
        "calibration_bins": [
            b.to_dict() for b in calibration_bins()
        ],
    }


__all__ = [
    "AUC_THRESHOLD", "V392Report",
    "build_frame_normalized_prediction_artifact",
    "build_report",
]
