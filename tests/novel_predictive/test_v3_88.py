"""v3.88 — predictive novel degeneracy tests."""
from __future__ import annotations

import json
import pathlib

from desi.novel_families import all_family_members
from desi.novel_predictive.forecast import (
    CALIBRATION_BIN_COUNT,
    calibration_bins, calibration_error,
    false_positive_rate, forecast_margin,
    optimal_threshold, predictive_auc, roc_auc,
)
from desi.novel_predictive.predict import (
    all_novel_pair_forecasts,
)
from desi.novel_predictive.report import (
    AUC_THRESHOLD,
    build_novel_family_predictive_artifact,
    build_report,
)


def test_pair_count_matches_combinations() -> None:
    """38 choose 2 = 703 novel pairs."""
    assert len(all_novel_pair_forecasts()) == 703


def test_score_equals_negative_distance() -> None:
    for p in all_novel_pair_forecasts()[:50]:
        assert p.score == round(-p.distance, 6)


def test_same_family_labels_match_family_map() -> None:
    fam = {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }
    for p in all_novel_pair_forecasts()[:50]:
        expected = fam[p.anchor_a] == fam[p.anchor_b]
        assert p.same_family == expected


def test_predictive_auc_in_unit_interval() -> None:
    assert 0.0 <= predictive_auc() <= 1.0


def test_predictive_auc_above_random() -> None:
    """Even on novel material we expect some
    signal - the score should beat random."""
    assert predictive_auc() > 0.5


def test_roc_auc_is_one_for_perfect_split() -> None:
    """Sanity test: a hand-crafted perfectly-
    separable input yields AUC == 1.0."""
    from desi.novel_predictive.predict import (
        NovelPairForecast,
    )
    fake = (
        NovelPairForecast(
            anchor_a="x", anchor_b="y",
            family_a="A", family_b="A",
            distance=0.0, score=1.0,
            same_family=True,
        ),
        NovelPairForecast(
            anchor_a="x", anchor_b="z",
            family_a="A", family_b="B",
            distance=1.0, score=0.0,
            same_family=False,
        ),
    )
    assert roc_auc(fake) == 1.0


def test_forecast_margin_value_present() -> None:
    """Forecast margin can be positive or negative;
    we just check it is finite."""
    m = forecast_margin()
    assert m == m  # not NaN
    assert -1e6 < m < 1e6


def test_false_positive_rate_in_unit_interval() -> None:
    fpr = false_positive_rate(optimal_threshold())
    assert 0.0 <= fpr <= 1.0


def test_calibration_bin_count_is_five() -> None:
    assert len(calibration_bins()) == (
        CALIBRATION_BIN_COUNT
    )


def test_calibration_error_in_unit_interval() -> None:
    assert 0.0 <= calibration_error() <= 1.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_pair_counts_sum_to_total() -> None:
    r = build_report()
    assert (
        r.same_family_pair_count
        + r.cross_family_pair_count
        == r.pair_count
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "NOVEL_DEGENERACY_PREDICTABLE",
        "NOVEL_DEGENERACY_WEAK_SIGNAL",
        "NOVEL_DEGENERACY_NOT_PREDICTABLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_concept_gate_auc_truth_recorded() -> None:
    r = build_report()
    if r.predictive_auc >= AUC_THRESHOLD:
        assert r.recommendation == (
            "NOVEL_DEGENERACY_PREDICTABLE"
        )
    elif r.predictive_auc > 0.5:
        assert r.recommendation == (
            "NOVEL_DEGENERACY_WEAK_SIGNAL"
        )
    else:
        assert r.recommendation == (
            "NOVEL_DEGENERACY_NOT_PREDICTABLE"
        )


def test_artifact_has_all_forecasts() -> None:
    art = build_novel_family_predictive_artifact()
    assert len(art["pair_forecasts"]) == 703


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_88" / "report.json").read_text(
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
