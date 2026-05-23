"""v3.82 — minimal feature detection tests."""
from __future__ import annotations

import json
import pathlib

from desi.minimal_features.ablation import (
    FeatureAblationKind,
    all_ablation_outcomes,
)
from desi.minimal_features.importance import (
    baseline_purity, feature_importance,
    minimal_cluster_accuracy,
    minimal_feature_set, proxy_score,
)
from desi.minimal_features.report import (
    build_minimal_feature_detection_artifact,
    build_report,
)


def test_six_ablation_kinds() -> None:
    """Pflichtmenge: closed set of 6 ablations."""
    assert len(
        list(FeatureAblationKind)
    ) == 6


def test_all_outcomes_use_three_or_fewer_clusters() -> None:
    """A single-dim drop never explodes the cluster
    count beyond the ground-truth class count."""
    for o in all_ablation_outcomes():
        assert 1 <= o.cluster_count <= 3


def test_branch_cost_is_most_important() -> None:
    """Dropping branch_cost destroys the high vs.
    bridge boundary."""
    imps = {
        f.dim: f.importance
        for f in feature_importance()
    }
    assert imps["branch_cost"] >= imps[
        "contradiction_load"
    ]
    assert imps["branch_cost"] > 0
    assert imps["contradiction_load"] > 0


def test_controls_have_zero_importance() -> None:
    """Zero-variance dims (frame_id,
    source_quality) must contribute zero
    importance."""
    imps = {
        f.dim: f.importance
        for f in feature_importance()
    }
    assert imps["frame_id"] == 0.0
    assert imps["source_quality"] == 0.0


def test_minimal_set_is_two_dims() -> None:
    """Two dims suffice: contradiction_load +
    branch_cost."""
    minimal = set(minimal_feature_set())
    assert minimal == {
        "branch_cost", "contradiction_load",
    }


def test_minimal_cluster_accuracy_is_baseline() -> None:
    assert minimal_cluster_accuracy() == (
        baseline_purity()
    )


def test_proxy_score_is_one() -> None:
    """The 2-dim minimal set is a perfect proxy."""
    assert proxy_score() == 1.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_minimal_proxy_found() -> None:
    assert build_report().recommendation == (
        "MINIMAL_PROXY_FOUND"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MINIMAL_PROXY_FOUND",
        "PROXY_FOUND_NOT_MINIMAL",
        "NO_MINIMAL_PROXY",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_all_six_ablations() -> None:
    art = build_minimal_feature_detection_artifact()
    assert len(art["ablation_outcomes"]) == 6
    assert len(art["feature_importance"]) == 6


def test_artifact_records_minimal_set() -> None:
    art = build_minimal_feature_detection_artifact()
    assert set(art["minimal_feature_set"]) == {
        "branch_cost", "contradiction_load",
    }


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_82" / "report.json").read_text(
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
