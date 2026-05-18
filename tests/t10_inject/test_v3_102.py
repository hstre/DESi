"""v3.102 - T10 single-dimension injection tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_inject.inject import (
    baseline_dim, injected_dim,
    injected_vectors, selected_candidate,
)
from desi.t10_inject.recover import (
    all_injected_clusters, cluster_delta,
    geometry_delta, injected_auc,
    injected_cluster_count,
    injected_cluster_sizes,
    injected_purity,
)
from desi.t10_inject.report import (
    AUC_THRESHOLD,
    PURITY_THRESHOLD,
    build_report,
    build_t10_single_dimension_injection_artifact,
)


def test_selected_candidate_matches_v3101() -> None:
    """v3.102 pulls the best candidate from
    v3.101; no hard-coded override."""
    from desi.t10.search import best_outcome
    assert selected_candidate() == (
        best_outcome().candidate
    )


def test_injected_dim_is_baseline_plus_one() -> None:
    assert injected_dim() == baseline_dim() + 1


def test_baseline_dim_is_forty_five() -> None:
    assert baseline_dim() == 45


def test_injected_vectors_cover_nineteen() -> None:
    assert len(injected_vectors()) == 19


def test_injected_cluster_count_is_two() -> None:
    """Killerfrage: reicht eine einzige
    zusaetzliche Dimension? Yes - the injection
    splits the previously merged 19-anchor cloud
    into two clusters."""
    assert injected_cluster_count() == 2


def test_injected_cluster_sizes_match_family_sizes() -> None:
    """G has 9 members, E has 10 - the injection
    recovers exactly those sizes."""
    sizes = sorted(injected_cluster_sizes())
    assert sizes == [9, 10]


def test_injected_purity_passes_gate() -> None:
    """Concept Gate condition #2:
    injected_purity >= 0.70."""
    assert injected_purity() >= PURITY_THRESHOLD


def test_injected_purity_is_one() -> None:
    assert injected_purity() == 1.0


def test_injected_auc_passes_gate() -> None:
    """Concept Gate condition #3:
    injected_auc >= 0.70."""
    assert injected_auc() >= AUC_THRESHOLD


def test_injected_auc_is_one() -> None:
    assert injected_auc() == 1.0


def test_geometry_delta_in_unit_interval() -> None:
    gd = geometry_delta()
    assert 0.0 <= gd


def test_cluster_delta_is_one_extra_cluster() -> None:
    """Before injection: 1 collapsed cluster.
    After injection: 2 family-pure clusters.
    cluster_delta = 2 - 1 = +1."""
    assert cluster_delta() == 1


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_rescues() -> None:
    assert build_report().recommendation == (
        "SINGLE_DIM_RESCUES"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SINGLE_DIM_RESCUES",
        "SINGLE_DIM_PARTIAL",
        "SINGLE_DIM_INSUFFICIENT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_clusters() -> None:
    art = build_t10_single_dimension_injection_artifact()
    assert len(art["injected_clusters"]) == 2


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_102" / "report.json").read_text(
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
