"""v3.91 — frame-normalized minimal feature tests."""
from __future__ import annotations

import json
import pathlib

from desi.frame_normalized_minimal.ablation import (
    best_minimal_feature_set,
    informative_subset_outcomes,
    marginal_frame_gain,
    normalized_predictive_auc,
    normalized_proxy_accuracy,
)
from desi.frame_normalized_minimal.minimal import (
    PROXY_DIMS,
    cluster_residual, residual_full,
    residual_projection,
)
from desi.frame_normalized_minimal.report import (
    PROXY_THRESHOLD,
    build_frame_normalized_minimal_features_artifact,
    build_report,
)


def test_proxy_dims_match_v382() -> None:
    """Proxy must remain the v3.82 minimal set."""
    assert set(PROXY_DIMS()) == {
        "branch_cost", "contradiction_load",
    }


def test_residual_full_count_is_thirty_eight() -> None:
    assert len(residual_full()) == 38


def test_residual_projection_zeros_dropped_dims() -> None:
    proxy = frozenset(PROXY_DIMS())
    from desi.epistemic_trajectory.state import (
        DIMENSION_NAMES,
    )
    keep_idx = set()
    for d in proxy:
        di = DIMENSION_NAMES.index(d)
        keep_idx.update(
            s * 9 + di for s in range(5)
        )
    vecs = residual_projection(proxy)
    for tid, v in vecs.items():
        for i, x in enumerate(v):
            if i not in keep_idx:
                assert x == 0.0


def test_normalized_proxy_accuracy_in_unit_interval() -> None:
    assert (
        0.0
        <= normalized_proxy_accuracy()
        <= 1.0
    )


def test_normalized_predictive_auc_in_unit_interval() -> None:
    assert 0.0 <= normalized_predictive_auc() <= 1.0


def test_normalized_predictive_auc_above_random() -> None:
    assert normalized_predictive_auc() > 0.5


def test_best_minimal_set_subset_of_informative() -> None:
    informative = {
        "branch_cost", "contradiction_load",
        "novelty",
    }
    for d in best_minimal_feature_set():
        assert d in informative


def test_best_minimal_set_is_proxy() -> None:
    """Both the v3.82 plateau search and the v3.91
    novel residual search converge on the same
    two-feature set."""
    assert set(
        best_minimal_feature_set(),
    ) == set(PROXY_DIMS())


def test_marginal_frame_gain_positive() -> None:
    """Removing frame must improve full-feature
    purity on novel material."""
    assert marginal_frame_gain() > 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PROXY_UNCOVERED_BY_NORMALIZATION",
        "PROXY_PARTIALLY_UNCOVERED_BY_NORMALIZATION",
        "PROXY_NOT_FRAME_HIDDEN",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_consistent_with_proxy_delta() -> None:
    r = build_report()
    if (
        r.normalized_proxy_accuracy
        >= PROXY_THRESHOLD
    ):
        assert r.recommendation == (
            "PROXY_UNCOVERED_BY_NORMALIZATION"
        )
    elif (
        r.normalized_proxy_accuracy
        > r.raw_proxy_accuracy
    ):
        assert r.recommendation == (
            "PROXY_PARTIALLY_UNCOVERED_BY_NORMALIZATION"
        )
    else:
        assert r.recommendation == (
            "PROXY_NOT_FRAME_HIDDEN"
        )


def test_informative_subset_outcomes_count() -> None:
    """3 informative dims → 7 non-empty subsets."""
    assert len(informative_subset_outcomes()) == 7


def test_proxy_subset_is_in_outcomes() -> None:
    proxy_tup = tuple(sorted(PROXY_DIMS()))
    outs = informative_subset_outcomes()
    proxy_outs = [
        o for o in outs if o.dims == proxy_tup
    ]
    assert len(proxy_outs) == 1


def test_artifact_lists_proxy_and_subsets() -> None:
    art = build_frame_normalized_minimal_features_artifact()
    assert art["proxy_dims"] == list(PROXY_DIMS())
    assert len(
        art["informative_subset_outcomes"],
    ) == 7


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_91" / "report.json").read_text(
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
