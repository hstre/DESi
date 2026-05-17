"""v3.84 — predictive degeneracy report.

Pflichtmetriken (directive § v3.84):

* ``predictive_auc``
* ``false_positive_rate``
* ``forecast_margin``
* ``calibration_error``
* ``replay_stability``

Concept Gate thresholds:

* ``PREDICTIVE_AUC_FLOOR``      = 0.70
* ``FPR_CEILING``               = 0.20
* ``CALIBRATION_ERROR_CEILING`` = 0.20
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..redundancy_masking.equivalence import (
    PROBE_RADIUS,
)
from .calibration import (
    calibration_bins, calibration_error,
)
from .forecast import (
    all_pair_forecasts, false_positive_rate,
    forecast_margin, optimal_threshold,
    predictive_auc,
)


PREDICTIVE_AUC_FLOOR: float = 0.70
FPR_CEILING: float = 0.20
CALIBRATION_ERROR_CEILING: float = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V384Report:
    probe_radius: float
    pair_count: int
    positive_pair_count: int
    negative_pair_count: int
    predictive_auc: float
    optimal_threshold: float
    false_positive_rate: float
    forecast_margin: float
    calibration_bins: tuple[dict, ...]
    calibration_error: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "pair_count": self.pair_count,
            "positive_pair_count":
                self.positive_pair_count,
            "negative_pair_count":
                self.negative_pair_count,
            "predictive_auc": self.predictive_auc,
            "optimal_threshold":
                self.optimal_threshold,
            "false_positive_rate":
                self.false_positive_rate,
            "forecast_margin": self.forecast_margin,
            "calibration_bins":
                list(self.calibration_bins),
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
    a = [
        p.to_dict() for p in all_pair_forecasts()
    ]
    b = [
        p.to_dict() for p in all_pair_forecasts()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V384Report:
    pairs = all_pair_forecasts()
    pos = sum(1 for p in pairs if p.same_class)
    neg = len(pairs) - pos
    auc = predictive_auc()
    thr = optimal_threshold()
    fpr = false_positive_rate(thr)
    margin = forecast_margin()
    bins = calibration_bins()
    cal = calibration_error()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        auc >= PREDICTIVE_AUC_FLOOR
        and fpr <= FPR_CEILING
        and cal <= CALIBRATION_ERROR_CEILING
        and margin > 0.0
    ):
        verdict = "PREDICTIVE_DEGENERACY_DETECTED"
    elif auc >= PREDICTIVE_AUC_FLOOR:
        verdict = "PREDICTIVE_DEGENERACY_PARTIAL"
    else:
        verdict = "PREDICTIVE_DEGENERACY_WEAK"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: pair_count {len(pairs)} "
        f"(pos {pos}, neg {neg})",
        f"{'PASS' if auc >= PREDICTIVE_AUC_FLOOR else 'FAIL'}: "
        f"predictive_auc {auc} "
        f"(floor {PREDICTIVE_AUC_FLOOR})",
        f"INFO: optimal_threshold {thr}",
        f"{'PASS' if fpr <= FPR_CEILING else 'FAIL'}: "
        f"false_positive_rate {fpr} "
        f"(ceiling {FPR_CEILING})",
        f"{'PASS' if margin > 0 else 'FAIL'}: "
        f"forecast_margin {margin}",
        f"INFO: calibration_bins "
        f"{[b.to_dict() for b in bins]}",
        f"{'PASS' if cal <= CALIBRATION_ERROR_CEILING else 'FAIL'}: "
        f"calibration_error {cal} "
        f"(ceiling {CALIBRATION_ERROR_CEILING})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V384Report(
        probe_radius=PROBE_RADIUS,
        pair_count=len(pairs),
        positive_pair_count=pos,
        negative_pair_count=neg,
        predictive_auc=auc,
        optimal_threshold=thr,
        false_positive_rate=fpr,
        forecast_margin=margin,
        calibration_bins=tuple(
            b.to_dict() for b in bins
        ),
        calibration_error=cal,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_predictive_degeneracy_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_84_predictive_degeneracy",
        "probe_radius": PROBE_RADIUS,
        "predictive_auc": predictive_auc(),
        "forecast_margin": forecast_margin(),
        "optimal_threshold": optimal_threshold(),
        "calibration_error": calibration_error(),
        "calibration_bins": [
            b.to_dict() for b in calibration_bins()
        ],
        "pair_forecasts": [
            p.to_dict()
            for p in all_pair_forecasts()
        ],
    }


__all__ = [
    "CALIBRATION_ERROR_CEILING", "FPR_CEILING",
    "PREDICTIVE_AUC_FLOOR", "V384Report",
    "build_predictive_degeneracy_artifact",
    "build_report",
]
