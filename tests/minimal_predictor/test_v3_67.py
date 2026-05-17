"""v3.67 — minimal predictor tests."""
from __future__ import annotations

import json
import pathlib

from desi.minimal_predictor.comparison import (
    best_model, evaluate_all_models, evaluate_model,
    marginal_gains,
)
from desi.minimal_predictor.models import (
    ModelKind, complexity_of, features_for,
)
from desi.minimal_predictor.report import (
    build_minimal_predictor_artifact, build_report,
)


def test_model_kinds_match_directive() -> None:
    expected = {
        "A_distance_only", "B_coverage_only",
        "C_distance_and_coverage",
        "D_all_features",
    }
    assert {k.value for k in ModelKind} == expected


def test_features_for_each_kind() -> None:
    assert features_for("A_distance_only") == (
        "distance",
    )
    assert features_for("B_coverage_only") == (
        "coverage_gain",
    )
    assert features_for(
        "C_distance_and_coverage",
    ) == ("distance", "coverage_gain")
    assert features_for("D_all_features") == (
        "distance", "coverage_gain",
        "heterogeneity", "diversity",
    )


def test_complexity_matches_feature_count() -> None:
    for k in ModelKind:
        assert complexity_of(k.value) == len(
            features_for(k.value),
        )


def test_evaluate_each_model() -> None:
    for k in ModelKind:
        ev = evaluate_model(k.value)
        assert ev.model_kind == k.value
        assert 0.0 <= ev.auc <= 1.0


def test_evaluate_all_models_count() -> None:
    assert len(evaluate_all_models()) == 4


def test_distance_only_auc_above_floor() -> None:
    """Empirical: A reaches AUC ~0.72 - just above
    the 0.70 directive floor."""
    ev = evaluate_model("A_distance_only")
    assert ev.auc > 0.70


def test_coverage_only_auc_perfect() -> None:
    """Coverage_gain alone reaches AUC 1.0 - the
    mechanical equivalence to the resonance
    definition."""
    ev = evaluate_model("B_coverage_only")
    assert ev.auc == 1.0


def test_distance_and_coverage_auc_perfect() -> None:
    ev = evaluate_model("C_distance_and_coverage")
    assert ev.auc == 1.0


def test_all_features_auc_perfect() -> None:
    ev = evaluate_model("D_all_features")
    assert ev.auc == 1.0


def test_marginal_gain_b_over_a_is_positive() -> None:
    """Adding coverage_gain to distance-only adds
    ~0.28 AUC."""
    gains = marginal_gains(evaluate_all_models())
    by_kind = {g["model_kind"]: g for g in gains}
    assert by_kind[
        "B_coverage_only"
    ]["marginal_gain"] > 0


def test_marginal_gain_c_and_d_zero() -> None:
    """Beyond coverage_gain, neither distance nor the
    other features add anything."""
    gains = marginal_gains(evaluate_all_models())
    by_kind = {g["model_kind"]: g for g in gains}
    assert by_kind[
        "C_distance_and_coverage"
    ]["marginal_gain"] == 0.0
    assert by_kind[
        "D_all_features"
    ]["marginal_gain"] == 0.0


def test_best_model_is_coverage_only() -> None:
    """Most parsimonious near-optimum: B alone hits
    AUC 1.0 and has complexity 1."""
    assert best_model(evaluate_all_models()) == (
        "B_coverage_only"
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_missing_required() -> None:
    """Honest empirical finding: best_model
    (B_coverage_only) does not include the
    distance feature, so the directive's
    Paper-11 final gate #4 FAILS at this sprint."""
    assert build_report().recommendation == (
        "MINIMAL_PREDICTOR_MISSING_REQUIRED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MINIMAL_PREDICTOR_INCLUDES_BOTH",
        "MINIMAL_PREDICTOR_MISSING_REQUIRED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_evaluations_count() -> None:
    art = build_minimal_predictor_artifact()
    assert len(art["evaluations"]) == 4
    assert len(art["marginal_gain"]) == 4


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_67" / "report.json").read_text(
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
