"""v3.65 — blind prediction tests."""
from __future__ import annotations

import json
import pathlib

from desi.predictive.blind_split import (
    TEST_STRIDE, folded_pairs,
    test_pairs as fetch_test_pairs,
    train_pairs as fetch_train_pairs,
)
from desi.predictive.predictor import (
    EvaluationResult, FEATURE_NAMES, evaluate,
    features, fit,
)
from desi.predictive.report import (
    PAPER11_FINAL_AUC_FLOOR,
    build_predictive_activation_artifact,
    build_report,
)


def test_test_stride_is_three() -> None:
    assert TEST_STRIDE == 3


def test_folded_pairs_total_is_190() -> None:
    assert len(folded_pairs()) == 190


def test_train_test_split() -> None:
    train = fetch_train_pairs()
    test = fetch_test_pairs()
    assert len(train) + len(test) == 190
    # 67/33 stride yields 127/63
    assert len(train) == 127
    assert len(test) == 63


def test_train_test_disjoint() -> None:
    train_ids = {(p.a, p.b) for p in fetch_train_pairs()}
    test_ids = {(p.a, p.b) for p in fetch_test_pairs()}
    assert not (train_ids & test_ids)


def test_feature_names_match_directive() -> None:
    """Directive: distance, coverage_gain,
    heterogeneity, diversity."""
    assert FEATURE_NAMES == (
        "distance", "coverage_gain",
        "heterogeneity", "diversity",
    )


def test_features_emits_all_four() -> None:
    p = fetch_train_pairs()[0]
    out = features(p)
    assert set(out.keys()) == set(FEATURE_NAMES)


def test_fit_returns_weights_for_all_features() -> None:
    model = fit(fetch_train_pairs())
    assert set(model.weights.keys()) == set(FEATURE_NAMES)


def test_fit_coverage_gain_weight_is_largest() -> None:
    """coverage_gain is the dominant discriminant
    feature because resonance is definitionally
    coverage-gain-driven."""
    model = fit(fetch_train_pairs())
    abs_weights = {
        f: abs(w) for f, w in model.weights.items()
    }
    assert (
        abs_weights["coverage_gain"]
        > max(
            abs_weights["distance"],
            abs_weights["heterogeneity"],
            abs_weights["diversity"],
        )
    )


def test_evaluate_returns_evaluation_result() -> None:
    model = fit(fetch_train_pairs())
    result = evaluate(model, fetch_test_pairs())
    assert isinstance(result, EvaluationResult)
    assert 0.0 <= result.auc <= 1.0
    assert 0.0 <= result.precision <= 1.0
    assert 0.0 <= result.recall <= 1.0
    assert 0.0 <= result.false_positive_rate <= 1.0


def test_blind_auc_meets_gate() -> None:
    """Paper-11 final gate #1: auc >= 0.70."""
    r = build_report()
    assert r.auc >= PAPER11_FINAL_AUC_FLOOR


def test_blind_auc_is_perfect() -> None:
    """With coverage_gain in the feature set, the
    predictor is mechanically perfect on this
    corpus."""
    assert build_report().auc == 1.0


def test_precision_perfect() -> None:
    assert build_report().precision == 1.0


def test_recall_perfect() -> None:
    assert build_report().recall == 1.0


def test_false_positive_rate_zero() -> None:
    assert build_report().false_positive_rate == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_passes() -> None:
    assert build_report().recommendation == (
        "BLIND_PREDICTION_PASSES"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "BLIND_PREDICTION_PASSES",
        "BLIND_PREDICTION_WEAK",
        "BLIND_PREDICTION_FAILED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_fold_records_count() -> None:
    art = build_predictive_activation_artifact()
    assert len(art["fold_records"]) == 190


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_65" / "report.json").read_text(
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
