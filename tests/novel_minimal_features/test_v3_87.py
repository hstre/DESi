"""v3.87 — minimal feature transfer tests."""
from __future__ import annotations

import json
import pathlib

from desi.minimal_features.importance import (
    minimal_feature_set as v382_minimal_set,
)
from desi.novel_minimal_features.minimal import (
    PROXY_DIMS, cluster_with_full,
    cluster_with_proxy,
    projected_novel_vectors,
)
from desi.novel_minimal_features.report import (
    PROXY_THRESHOLD,
    build_novel_family_proxy_artifact,
    build_report,
)
from desi.novel_minimal_features.transfer import (
    baseline_full_purity, feature_stability,
    new_informative_dims, proxy_accuracy,
    proxy_gap,
)


def test_proxy_dims_match_v382_minimal_set() -> None:
    """The v3.87 proxy must come from v3.82, not
    be hard-coded - that's the discipline that
    keeps drift visible."""
    assert set(PROXY_DIMS()) == set(v382_minimal_set())


def test_proxy_dims_are_branch_cost_and_contradiction_load() -> None:
    """Sanity: directive states proxy =
    {branch_cost, contradiction_load}."""
    assert set(PROXY_DIMS()) == {
        "branch_cost", "contradiction_load",
    }


def test_projection_zeros_dropped_dimensions() -> None:
    """When we keep ONLY branch_cost +
    contradiction_load, the other 7 dimension
    indices must be zero in every vector."""
    from desi.epistemic_trajectory.state import (
        DIMENSION_NAMES,
    )
    keep_idx = set()
    for d in PROXY_DIMS():
        di = DIMENSION_NAMES.index(d)
        keep_idx.update(
            s * 9 + di for s in range(5)
        )
    vecs = projected_novel_vectors(
        frozenset(PROXY_DIMS()),
    )
    for tid, v in vecs.items():
        for i, x in enumerate(v):
            if i not in keep_idx:
                assert x == 0.0


def test_proxy_accuracy_in_unit_interval() -> None:
    assert 0.0 <= proxy_accuracy() <= 1.0


def test_baseline_full_purity_matches_v386() -> None:
    """The v3.87 full-feature baseline must equal
    the v3.86 cluster purity (both run on the same
    novel anchor pool with full features)."""
    from desi.novel_family_cluster.cluster import (
        cluster_purity as v386_purity,
        all_novel_blind_clusters,
    )
    assert baseline_full_purity() == v386_purity(
        all_novel_blind_clusters(),
    )


def test_proxy_beats_or_matches_full() -> None:
    """Killerfrage: Sind branch_cost +
    contradiction_load universell? At minimum the
    proxy should not be WORSE than the full
    feature space."""
    assert proxy_accuracy() >= baseline_full_purity()


def test_proxy_gap_sign_matches_difference() -> None:
    assert proxy_gap() == round(
        baseline_full_purity() - proxy_accuracy(),
        6,
    )


def test_feature_stability_in_unit_interval() -> None:
    assert 0.0 <= feature_stability() <= 1.0


def test_new_informative_dims_excludes_proxy_dims() -> None:
    proxy = set(PROXY_DIMS())
    for d in new_informative_dims():
        assert d.dim not in proxy


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PROXY_TRANSFERS",
        "PROXY_PARTIAL_TRANSFER",
        "PROXY_DOES_NOT_TRANSFER",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_concept_gate_proxy_accuracy_truth_recorded() -> None:
    r = build_report()
    if r.proxy_accuracy >= PROXY_THRESHOLD:
        assert r.recommendation == "PROXY_TRANSFERS"
    elif r.proxy_gap <= 0.0:
        assert r.recommendation == (
            "PROXY_PARTIAL_TRANSFER"
        )
    else:
        assert r.recommendation == (
            "PROXY_DOES_NOT_TRANSFER"
        )


def test_proxy_clusters_partition_all_anchors() -> None:
    cls = cluster_with_proxy()
    total = sum(len(c.members) for c in cls)
    assert total == 38


def test_full_clusters_partition_all_anchors() -> None:
    cls = cluster_with_full()
    total = sum(len(c.members) for c in cls)
    assert total == 38


def test_artifact_lists_both_clusterings() -> None:
    art = build_novel_family_proxy_artifact()
    assert art["proxy_dims"] == list(PROXY_DIMS())
    assert len(art["proxy_clusters"]) == len(
        cluster_with_proxy(),
    )
    assert len(art["full_clusters"]) == len(
        cluster_with_full(),
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_87" / "report.json").read_text(
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
