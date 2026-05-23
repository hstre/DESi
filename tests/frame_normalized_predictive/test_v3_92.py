"""v3.92 — frame-normalized predictive tests."""
from __future__ import annotations

import json
import pathlib

from desi.frame_normalized_predictive.forecast import (
    CALIBRATION_BIN_COUNT,
    calibration_bins, calibration_error,
    forecast_margin, frame_normalized_auc,
    frame_normalized_fpr, optimal_threshold,
    roc_auc,
)
from desi.frame_normalized_predictive.predict import (
    all_normalized_pair_forecasts,
)
from desi.frame_normalized_predictive.report import (
    AUC_THRESHOLD,
    build_frame_normalized_prediction_artifact,
    build_report,
)


def test_pair_count_matches_combinations() -> None:
    assert len(all_normalized_pair_forecasts()) == 703


def test_score_equals_negative_distance() -> None:
    for p in all_normalized_pair_forecasts()[:50]:
        assert p.score == round(-p.distance, 6)


def test_frame_normalized_auc_in_unit_interval() -> None:
    assert 0.0 <= frame_normalized_auc() <= 1.0


def test_frame_normalized_auc_above_random() -> None:
    assert frame_normalized_auc() > 0.5


def test_frame_normalized_auc_beats_raw() -> None:
    """Normalization must improve over the v3.88
    raw AUC."""
    from desi.novel_predictive.forecast import (
        predictive_auc as raw_auc,
    )
    assert frame_normalized_auc() > raw_auc()


def test_frame_normalized_auc_passes_gate() -> None:
    """Concept Gate condition #4. This sprint's
    central PASS - the only discrimination gate
    that the v3.85-v3.92 chain clears on novel
    material."""
    assert frame_normalized_auc() >= AUC_THRESHOLD


def test_roc_auc_perfect_on_separable_input() -> None:
    from desi.frame_normalized_predictive.predict import (
        FrameNormalizedPairForecast,
    )
    fake = (
        FrameNormalizedPairForecast(
            anchor_a="x", anchor_b="y",
            family_a="A", family_b="A",
            distance=0.0, score=1.0,
            same_family=True,
        ),
        FrameNormalizedPairForecast(
            anchor_a="x", anchor_b="z",
            family_a="A", family_b="B",
            distance=1.0, score=0.0,
            same_family=False,
        ),
    )
    assert roc_auc(fake) == 1.0


def test_calibration_bin_count_is_five() -> None:
    assert len(calibration_bins()) == (
        CALIBRATION_BIN_COUNT
    )


def test_calibration_error_lower_than_v388() -> None:
    """Normalization should also improve
    calibration."""
    from desi.novel_predictive.forecast import (
        calibration_error as raw_ce,
    )
    assert calibration_error() < raw_ce()


def test_false_positive_rate_lower_than_v388() -> None:
    from desi.novel_predictive.forecast import (
        false_positive_rate as raw_fpr,
        optimal_threshold as raw_opt,
    )
    assert (
        frame_normalized_fpr(optimal_threshold())
        < raw_fpr(raw_opt())
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "FRAME_NORMALIZED_DEGENERACY_PREDICTABLE",
        "FRAME_NORMALIZED_DEGENERACY_WEAK_GAIN",
        "FRAME_NORMALIZED_DEGENERACY_NO_GAIN",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_consistent_with_auc() -> None:
    r = build_report()
    if r.frame_normalized_auc >= AUC_THRESHOLD:
        assert r.recommendation == (
            "FRAME_NORMALIZED_DEGENERACY_PREDICTABLE"
        )
    elif (
        r.frame_normalized_auc
        > r.raw_predictive_auc
    ):
        assert r.recommendation == (
            "FRAME_NORMALIZED_DEGENERACY_WEAK_GAIN"
        )
    else:
        assert r.recommendation == (
            "FRAME_NORMALIZED_DEGENERACY_NO_GAIN"
        )


def test_pair_counts_sum_to_total() -> None:
    r = build_report()
    assert (
        r.same_family_pair_count
        + r.cross_family_pair_count
        == r.pair_count
    )


def test_artifact_has_all_forecasts() -> None:
    art = build_frame_normalized_prediction_artifact()
    assert len(art["pair_forecasts"]) == 703


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_92" / "report.json").read_text(
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
