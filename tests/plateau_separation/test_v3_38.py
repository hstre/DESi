"""v3.38 — feature-separation tests."""
from __future__ import annotations

import json
import pathlib

from desi.plateau_separation.boundary import (
    PLATEAU_LABEL, RESCUE_LABEL, all_feature_splits,
    best_separating_split, best_split_for_feature,
    support_final_split,
)
from desi.plateau_separation.clustering import (
    assign_clusters, connected_components, one_nn_edges,
)
from desi.plateau_separation.distance import (
    euclidean, overlap_rate, pairwise_distances,
    trajectory_vector,
)
from desi.plateau_separation.report import (
    MIN_SEPARABILITY, _gather_items, build_report,
    build_separability_map_artifact,
    build_separation_artifact,
)


def test_labels_match_directive() -> None:
    assert PLATEAU_LABEL == "plateau"
    assert RESCUE_LABEL == "causal_leap"


def test_euclidean_basic() -> None:
    assert euclidean((0.0, 0.0), (3.0, 4.0)) == 5.0
    assert euclidean((1.0,), (1.0,)) == 0.0


def test_trajectory_vector_length_45() -> None:
    items, sbi, _ = _gather_items()
    for tid, _, vec in items:
        assert len(vec) == 9 * len(sbi[tid])


def test_pairwise_distances_no_self_no_double() -> None:
    items, _, _ = _gather_items()
    ds = pairwise_distances(items)
    expected = len(items) * (len(items) - 1) // 2
    assert len(ds) == expected


def test_overlap_rate_is_zero() -> None:
    items, _, _ = _gather_items()
    # No two cross-class trajectories are bit-identical.
    assert overlap_rate(items) == 0.0


def test_connected_components_partition() -> None:
    parts = connected_components(4, ((0, 1), (2, 3)))
    assert parts == ((0, 1), (2, 3))


def test_one_nn_edges_symmetric() -> None:
    vecs = ((0.0,), (1.0,), (2.0,), (10.0,))
    edges = one_nn_edges(vecs)
    for a, b in edges:
        assert a < b


def test_assign_clusters_pure_on_movers() -> None:
    items, _, _ = _gather_items()
    clusters = assign_clusters(items)
    for c in clusters:
        assert c.is_pure


def test_best_split_for_feature_returns_high_accuracy() -> None:
    items, sbi, _ = _gather_items()
    s = best_split_for_feature("frame_id", 2, items, sbi)
    assert s.accuracy == 1.0


def test_best_separator_is_pre_audit() -> None:
    """Tied perfect separators: pre-audit features win
    over the final-state verdict feature."""
    items, sbi, n = _gather_items()
    splits = all_feature_splits(items, sbi, n)
    best = best_separating_split(splits)
    assert best.accuracy == 1.0
    assert best.state_index < n - 1


def test_support_final_accuracy_is_one() -> None:
    """The verdict is the final support_state, so by
    construction this separator is perfect."""
    items, sbi, n = _gather_items()
    splits = all_feature_splits(items, sbi, n)
    fs = support_final_split(splits, n)
    assert fs.accuracy == 1.0


def test_at_least_three_pre_audit_separators() -> None:
    """frame_id at indices 2 and 3 plus novelty at
    index 2 all separate the two groups perfectly."""
    assert build_report().pre_audit_perfect_separator_count >= 3


def test_separability_meets_gate() -> None:
    """Paper-10 v3 gate #3: separability >= 0.70."""
    assert build_report().separability >= MIN_SEPARABILITY


def test_manifold_count_is_two() -> None:
    """Disjoint geometric structures: classes do not
    share any 1-NN component, and both classes are
    populated."""
    assert build_report().manifold_count == 2


def test_cluster_purity_is_one() -> None:
    assert build_report().cluster_purity == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PLATEAU_AND_RESCUE_SEPARABLE",
        "PLATEAU_AND_RESCUE_PARTIALLY_SEPARABLE",
        "HALT_LOW_SEPARABILITY",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_full_universe() -> None:
    art = build_separation_artifact()
    assert len(art["items"]) == 34
    assert len({i["class"] for i in art["items"]}) == 2


def test_separability_map_records_all_features() -> None:
    art = build_separability_map_artifact()
    # 9 dimensions x 5 states = 45 splits
    assert len(art["splits"]) == 9 * 5


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_38" / "report.json").read_text(
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
