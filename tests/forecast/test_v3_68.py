"""v3.68 — causal forecast tests."""
from __future__ import annotations

import json
import pathlib

from desi.forecast.forecast import (
    EARLY_WARNING_STEPS, PRE_ACTIVATION_FEATURES,
    run_forecast, trained_forecast_model,
)
from desi.forecast.report import (
    FORECAST_ACCURACY_FLOOR,
    build_activation_forecast_artifact, build_report,
)


def test_pre_activation_features_excludes_coverage() -> None:
    """coverage_gain is post-activation by definition;
    the forecast must use only pre-activation
    features."""
    assert PRE_ACTIVATION_FEATURES == (
        "distance", "heterogeneity", "diversity",
    )
    assert "coverage_gain" not in (
        PRE_ACTIVATION_FEATURES
    )


def test_early_warning_steps_is_four() -> None:
    """Four pre-audit states per plateau trajectory
    (n=5, audit fires at index n-1=4, so warning
    horizon is 4)."""
    assert EARLY_WARNING_STEPS == 4


def test_trained_model_uses_pre_activation_features() -> None:
    model = trained_forecast_model()
    assert set(model.feature_names) == set(
        PRE_ACTIVATION_FEATURES,
    )


def test_forecast_accuracy_meets_floor() -> None:
    """Paper-11 final gate #5: forecast_accuracy
    >= 0.70."""
    f = run_forecast()
    assert f.forecast_accuracy >= (
        FORECAST_ACCURACY_FLOOR
    )


def test_forecast_accuracy_empirical_value() -> None:
    """Empirical: 45 of 63 test pairs classified
    correctly = 0.714."""
    f = run_forecast()
    assert f.forecast_accuracy == 0.714286


def test_forecast_auc_below_floor() -> None:
    """The pre-activation AUC (0.674) is below the
    0.70 floor; the gate passes by accuracy at the
    trained threshold, not by AUC. Honest finding."""
    f = run_forecast()
    assert f.evaluation.auc < (
        FORECAST_ACCURACY_FLOOR
    )


def test_calibration_error_small() -> None:
    f = run_forecast()
    assert f.calibration_error < 0.10


def test_predicted_positives_count() -> None:
    f = run_forecast()
    assert f.predicted_positives == 30


def test_actual_positives_count() -> None:
    """Test fold has 26 resonant pairs out of 63."""
    f = run_forecast()
    assert f.actual_positives == 26


def test_forecast_replay_stability_is_one() -> None:
    assert build_report().forecast_replay_stability == 1.0


def test_recommendation_is_usable() -> None:
    assert build_report().recommendation == (
        "FORECAST_USABLE"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "FORECAST_USABLE",
        "FORECAST_BELOW_FLOOR",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_has_forecast_block() -> None:
    art = build_activation_forecast_artifact()
    assert "forecast" in art
    assert "pre_activation_features" in art


def test_paper11_final_gate_summary() -> None:
    """All six Paper-11 final gates evaluated end-to-
    end. Gate #4 is the empirical FAILURE."""
    from desi.minimal_predictor.report import (
        build_report as v367,
    )
    from desi.oos_predictive.report import (
        MAX_TRANSFER_GAP, build_report as v366,
    )
    from desi.predictive.report import (
        PAPER11_FINAL_AUC_FLOOR,
        build_report as v365,
    )
    r65 = v365()
    r66 = v366()
    r67 = v367()
    r68 = build_report()
    # Gate 1: auc >= 0.70
    assert r65.auc >= PAPER11_FINAL_AUC_FLOOR
    # Gate 2: oos_auc >= 0.70
    assert r66.oos_auc >= PAPER11_FINAL_AUC_FLOOR
    # Gate 3: |transfer_gap| <= 0.20
    assert abs(r66.transfer_gap) <= MAX_TRANSFER_GAP
    # Gate 4: best_model includes distance + coverage
    #         (FAILS empirically - best_model is
    #         B_coverage_only)
    assert "distance" not in (
        r67.best_model_features
    )  # documents the failure
    # Gate 5: forecast_accuracy >= 0.70
    assert r68.forecast_accuracy >= (
        FORECAST_ACCURACY_FLOOR
    )
    # Gate 6: replay stability across all sprints
    assert r65.replay_stability == 1.0
    assert r66.replay_stability == 1.0
    assert r67.replay_stability == 1.0
    assert r68.forecast_replay_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_68" / "report.json").read_text(
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
