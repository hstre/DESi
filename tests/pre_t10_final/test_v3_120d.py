"""v3.120d - final pre-T10 rule tests."""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_final.decision import (
    _DRIFT_CEILING,
    _FAR_CEILING,
    _TPR_FLOOR,
    gate_failing_conditions,
    gate_passes_all,
)
from desi.pre_t10_final.report import (
    build_pre_t10_final_rule_artifact,
    build_report,
)
from desi.pre_t10_final.rule import (
    calibration_window_exists,
    final_adverse_flips,
    final_far,
    final_false_negative_rate,
    final_historical_gate_flip_count,
    final_rule_roi,
    final_threshold,
    final_threshold_drift,
    final_tpr,
)


def test_final_tpr_is_one() -> None:
    """Concept Gate condition #2:
    final_tpr == 1.0 PASSES."""
    assert final_tpr() >= _TPR_FLOOR


def test_final_far_above_ceiling() -> None:
    """Concept Gate condition #1:
    final_far <= 0.10 FAILS by 0.011."""
    assert final_far() > _FAR_CEILING


def test_threshold_drift_above_ceiling() -> None:
    """Concept Gate condition #3:
    threshold_drift <= 0.05 FAILS - bootstrap
    drift is 0.23."""
    assert final_threshold_drift() > (
        _DRIFT_CEILING
    )


def test_false_negative_rate_is_zero() -> None:
    """Concept Gate condition #4:
    false_negative_rate == 0 PASSES."""
    assert final_false_negative_rate() == 0.0


def test_historical_gate_flips_zero() -> None:
    """Concept Gate condition #5:
    historical_gate_flip_count == 0 PASSES."""
    assert (
        final_historical_gate_flip_count() == 0
    )


def test_adverse_flips_zero() -> None:
    """Stress replay produced no adverse flips."""
    assert final_adverse_flips() == 0


def test_rule_roi_positive() -> None:
    assert final_rule_roi() > 0.0


def test_calibration_window_empty() -> None:
    """Confirmed by v3.120a."""
    assert calibration_window_exists() is False


def test_gate_passes_all_is_false() -> None:
    """Honest finding: 2 of 6 gates fail."""
    assert gate_passes_all() is False


def test_failing_conditions_include_far_and_drift() -> None:
    failing = set(gate_failing_conditions())
    assert "final_far" in failing
    assert "threshold_drift" in failing


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PRE_T10_ACTIVATED",
        "PRE_T10_EXPERIMENTAL",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_experimental() -> None:
    """Killerfrage: darf Pre-T10 jetzt offiziell
    vor jede Expansion? NEIN - the strict
    Concept Gate keeps it experimental."""
    assert build_report().recommendation == (
        "PRE_T10_EXPERIMENTAL"
    )


def test_artifact_has_all_metrics() -> None:
    art = build_pre_t10_final_rule_artifact()
    keys = {
        "final_threshold", "final_far",
        "final_tpr", "threshold_drift",
        "adverse_flips",
        "false_negative_rate",
        "rule_roi",
        "historical_gate_flip_count",
        "calibration_window_exists",
        "gate_passes_all",
        "failing_conditions",
    }
    assert keys <= set(art.keys())


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_120d" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable
