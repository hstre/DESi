"""v3.88 — predictive novel degeneracy report.

Pflichtmetriken (directive § v3.88):

* ``predictive_auc``
* ``false_positive_rate``
* ``forecast_margin``
* ``calibration_error``
* ``replay_stability``

Concept gate (§ v3.88): ``predictive_auc >= 0.70``
(condition #5 of the sprint Concept Gate).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .forecast import (
    calibration_bins, calibration_error,
    false_positive_rate, forecast_margin,
    optimal_threshold, predictive_auc,
)
from .predict import (
    all_novel_pair_forecasts,
)


AUC_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V388Report:
    pair_count: int
    same_family_pair_count: int
    cross_family_pair_count: int
    predictive_auc: float
    forecast_margin: float
    optimal_threshold: float
    false_positive_rate: float
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
            "predictive_auc": self.predictive_auc,
            "forecast_margin":
                self.forecast_margin,
            "optimal_threshold":
                self.optimal_threshold,
            "false_positive_rate":
                self.false_positive_rate,
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
        predictive_auc(), forecast_margin(),
        optimal_threshold(),
        calibration_error(),
    )
    b = (
        predictive_auc(), forecast_margin(),
        optimal_threshold(),
        calibration_error(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V388Report:
    pairs = all_novel_pair_forecasts()
    pos = sum(1 for p in pairs if p.same_family)
    neg = sum(1 for p in pairs if not p.same_family)
    auc = predictive_auc()
    margin = forecast_margin()
    thr = optimal_threshold()
    fpr = false_positive_rate(thr)
    cerr = calibration_error()
    bins = calibration_bins()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif auc >= AUC_THRESHOLD:
        verdict = "NOVEL_DEGENERACY_PREDICTABLE"
    elif auc > 0.5:
        verdict = "NOVEL_DEGENERACY_WEAK_SIGNAL"
    else:
        verdict = "NOVEL_DEGENERACY_NOT_PREDICTABLE"

    rationale = (
        f"INFO: pair_count {len(pairs)} "
        f"(positives={pos}, negatives={neg})",
        f"{'PASS' if auc >= AUC_THRESHOLD else 'FAIL'}: "
        f"predictive_auc {auc} "
        f"(threshold {AUC_THRESHOLD})",
        f"INFO: forecast_margin {margin} "
        f"(positive ⇒ fully separable)",
        f"INFO: optimal_threshold {thr}",
        f"INFO: false_positive_rate {fpr}",
        f"INFO: calibration_error {cerr}",
        f"INFO: calibration_bins "
        f"{[b.to_dict() for b in bins]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V388Report(
        pair_count=len(pairs),
        same_family_pair_count=pos,
        cross_family_pair_count=neg,
        predictive_auc=auc,
        forecast_margin=margin,
        optimal_threshold=thr,
        false_positive_rate=fpr,
        calibration_error=cerr,
        calibration_bins=tuple(
            b.to_dict() for b in bins
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_novel_family_predictive_artifact(
) -> dict[str, object]:
    pairs = all_novel_pair_forecasts()
    return {
        "schema_version":
            "v3_88_novel_family_predictive",
        "pair_count": len(pairs),
        "predictive_auc": predictive_auc(),
        "forecast_margin": forecast_margin(),
        "optimal_threshold": optimal_threshold(),
        "false_positive_rate":
            false_positive_rate(
                optimal_threshold(),
            ),
        "calibration_error": calibration_error(),
        "pair_forecasts": [
            p.to_dict() for p in pairs
        ],
        "calibration_bins": [
            b.to_dict() for b in calibration_bins()
        ],
    }


__all__ = [
    "AUC_THRESHOLD", "V388Report",
    "build_novel_family_predictive_artifact",
    "build_report",
]
