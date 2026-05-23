"""v3.57 — content/method decomposition tests."""
from __future__ import annotations

import json
import pathlib

from desi.content_method.decompose import (
    cluster_assignments, cluster_count,
    cohort_features, cohort_purity,
    content_method_overlap, replay_stability,
    within_cohort_overlap,
)
from desi.content_method.features import (
    CONTENT_DIMS, METHOD_DIMS, content_state,
    content_vector, method_state, method_vector,
)
from desi.content_method.report import (
    MAX_CONTENT_METHOD_OVERLAP, build_report,
    build_content_method_decomposition_artifact,
)
from desi.epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from desi.field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)


def test_content_method_partition_disjoint() -> None:
    assert set(CONTENT_DIMS) & set(METHOD_DIMS) == set()


def test_content_method_partition_exhaustive() -> None:
    assert (
        set(CONTENT_DIMS) | set(METHOD_DIMS)
    ) == set(DIMENSION_NAMES)


def test_content_dim_count_is_five() -> None:
    assert len(CONTENT_DIMS) == 5


def test_method_dim_count_is_four() -> None:
    assert len(METHOD_DIMS) == 4


def test_content_state_length() -> None:
    t = collect_plateau_anchors()[0]
    assert len(content_state(t.states[0])) == 5


def test_method_state_length() -> None:
    t = collect_plateau_anchors()[0]
    assert len(method_state(t.states[0])) == 4


def test_content_vector_length_per_trajectory() -> None:
    t = collect_plateau_anchors()[0]
    assert len(content_vector(t.states)) == 5 * len(
        t.states,
    )


def test_method_vector_length_per_trajectory() -> None:
    t = collect_plateau_anchors()[0]
    assert len(method_vector(t.states)) == 4 * len(
        t.states,
    )


def test_cohort_features_universe_size() -> None:
    feats = cohort_features()
    assert len(feats) == 20 + 145


def test_cohort_features_split() -> None:
    feats = cohort_features()
    plat = sum(1 for f in feats if f.cohort == "plateau")
    leak = sum(1 for f in feats if f.cohort == "leakage")
    assert plat == 20
    assert leak == 145


def test_cluster_assignments_valid_subspaces() -> None:
    assert len(cluster_assignments("content")) == 165
    assert len(cluster_assignments("method")) == 165


def test_cluster_assignments_invalid_subspace_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        cluster_assignments("not_a_subspace")


def test_cluster_counts_positive() -> None:
    assert cluster_count("content") > 0
    assert cluster_count("method") > 0


def test_content_cluster_count_empirical() -> None:
    """Empirical pin: content subspace partitions the
    165-trajectory universe into 12 1-NN components."""
    assert cluster_count("content") == 12


def test_method_cluster_count_empirical() -> None:
    assert cluster_count("method") == 5


def test_cohort_purity_perfect_in_both_subspaces() -> None:
    assert cohort_purity("content") == 1.0
    assert cohort_purity("method") == 1.0


def test_content_method_overlap_high_in_this_corpus() -> None:
    """Honest empirical finding: content and method
    subspaces produce nearly identical cluster
    partitions. Overlap fails Concept Gate #2."""
    overlap = build_report().content_method_overlap
    assert overlap >= MAX_CONTENT_METHOD_OVERLAP
    assert overlap > 0.99


def test_within_cohort_overlap_also_high() -> None:
    """Even removing the cohort-split confound, the
    content and method partitions agree on within-
    cohort pairs."""
    assert build_report().within_cohort_overlap > 0.99


def test_decomposition_replay_stability_is_one() -> None:
    """Concept Gate #1: deterministic replay."""
    assert build_report().decomposition_replay_stability == 1.0
    assert replay_stability() == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CONTENT_METHOD_SEPARABLE",
        "CONTENT_METHOD_PARTIAL_OVERLAP",
        "CONTENT_METHOD_ENTANGLED",
        "HALT_DECOMPOSITION_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_partial_overlap() -> None:
    """overlap ~ 0.994 lies in (0.70, 1.00) -> the
    'partial overlap' verdict."""
    assert build_report().recommendation == (
        "CONTENT_METHOD_PARTIAL_OVERLAP"
    )


def test_artifact_records_each_trajectory() -> None:
    art = build_content_method_decomposition_artifact()
    assert art["trajectory_count"] == 165
    assert len(art["rows"]) == 165


def test_artifact_dimension_lists() -> None:
    art = build_content_method_decomposition_artifact()
    assert art["content_dims"] == list(CONTENT_DIMS)
    assert art["method_dims"] == list(METHOD_DIMS)


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_57" / "report.json").read_text(
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
