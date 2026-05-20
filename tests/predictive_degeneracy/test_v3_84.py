"""v3.84 — predictive degeneracy tests."""
from __future__ import annotations

import json
import pathlib

from desi.predictive_degeneracy.calibration import (
    CALIBRATION_BIN_COUNT, calibration_bins,
    calibration_error,
)
from desi.predictive_degeneracy.forecast import (
    all_pair_forecasts, false_positive_rate,
    forecast_margin, optimal_threshold,
    predictive_auc,
)
from desi.predictive_degeneracy.report import (
    CALIBRATION_ERROR_CEILING, FPR_CEILING,
    PREDICTIVE_AUC_FLOOR,
    build_predictive_degeneracy_artifact,
    build_report,
)


def test_pair_count() -> None:
    """20 choose 2 = 190 pairs."""
    assert len(all_pair_forecasts()) == 190


def test_positive_pair_count() -> None:
    """62 same-class pairs from v3.79: C(8,2) +
    C(8,2) + C(4,2) = 28 + 28 + 6 = 62."""
    pos = sum(
        1 for p in all_pair_forecasts()
        if p.same_class
    )
    assert pos == 62


def test_predictive_auc_is_one() -> None:
    """Killerfrage: distance separates same-class
    from cross-class pairs perfectly."""
    assert predictive_auc() == 1.0


def test_predictive_auc_meets_floor() -> None:
    assert predictive_auc() >= PREDICTIVE_AUC_FLOOR


def test_forecast_margin_is_positive() -> None:
    """Lowest same-class score > highest
    cross-class score."""
    assert forecast_margin() > 0


def test_false_positive_rate_is_zero_at_optimum() -> None:
    assert false_positive_rate(
        optimal_threshold(),
    ) == 0.0


def test_false_positive_rate_meets_ceiling() -> None:
    assert false_positive_rate(
        optimal_threshold(),
    ) <= FPR_CEILING


def test_calibration_bin_count() -> None:
    bins = calibration_bins()
    assert len(bins) == CALIBRATION_BIN_COUNT


def test_calibration_error_meets_ceiling() -> None:
    assert calibration_error() <= (
        CALIBRATION_ERROR_CEILING
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_detected() -> None:
    assert build_report().recommendation == (
        "PREDICTIVE_DEGENERACY_DETECTED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PREDICTIVE_DEGENERACY_DETECTED",
        "PREDICTIVE_DEGENERACY_PARTIAL",
        "PREDICTIVE_DEGENERACY_WEAK",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_all_pairs() -> None:
    art = build_predictive_degeneracy_artifact()
    assert len(art["pair_forecasts"]) == 190
    assert len(art["calibration_bins"]) == (
        CALIBRATION_BIN_COUNT
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_84" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
