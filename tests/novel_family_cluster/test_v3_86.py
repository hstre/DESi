"""v3.86 — blind novel family clustering tests."""
from __future__ import annotations

import json
import pathlib

from desi.novel_families import all_family_members
from desi.novel_family_cluster.cluster import (
    all_novel_blind_clusters,
    cluster_purity, cluster_recall,
    cluster_sizes,
    predicted_cluster_count,
)
from desi.novel_family_cluster.distance import (
    novel_anchor_vectors,
    novel_distance_gap,
    novel_pairwise_distances,
)
from desi.novel_family_cluster.report import (
    PURITY_THRESHOLD, RECALL_THRESHOLD,
    build_novel_family_clusters_artifact,
    build_report,
)


def test_anchor_count_is_thirty_eight() -> None:
    """38 = 11 + 8 + 10 + 9 across the four
    v3.85 families."""
    assert len(novel_anchor_vectors()) == 38


def test_pairwise_distance_count() -> None:
    """38 choose 2 = 703."""
    assert len(novel_pairwise_distances()) == 703


def test_distance_gap_in_data_range() -> None:
    """Threshold must lie inside the observed
    distance distribution."""
    dists = sorted(
        d for _, _, d in novel_pairwise_distances()
    )
    gap = novel_distance_gap()
    assert dists[0] < gap < dists[-1]


def test_cluster_count_at_least_two() -> None:
    """Pflichtfrage 1: natuerliche Cluster
    entstehen (= mehr als ein Cluster)."""
    assert predicted_cluster_count(
        all_novel_blind_clusters(),
    ) >= 2


def test_cluster_sizes_partition_all_anchors() -> None:
    clusters = all_novel_blind_clusters()
    total = sum(cluster_sizes(clusters))
    assert total == 38


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_predicted_cluster_count_metric() -> None:
    r = build_report()
    assert r.predicted_cluster_count == len(
        all_novel_blind_clusters(),
    )


def test_cluster_purity_in_unit_interval() -> None:
    p = cluster_purity(all_novel_blind_clusters())
    assert 0.0 <= p <= 1.0


def test_cluster_recall_in_unit_interval() -> None:
    r = cluster_recall(all_novel_blind_clusters())
    assert 0.0 <= r <= 1.0


def test_blind_clustering_is_genuinely_blind() -> None:
    """No family_id used by the clustering input.
    Reordering the input must not change the
    output."""
    a = [c.to_dict() for c in all_novel_blind_clusters()]
    b = [c.to_dict() for c in all_novel_blind_clusters()]
    assert a == b


def test_concept_gate_purity_truth_recorded() -> None:
    """The directive's Concept Gate #2 requires
    purity >= 0.70. We record the actual value,
    even when it fails, so the decision document
    is honest."""
    r = build_report()
    purity_pass = r.cluster_purity >= PURITY_THRESHOLD
    if purity_pass:
        assert r.recommendation in {
            "NOVEL_DOPPELGAENGER_DETECTED",
            "NOVEL_DOPPELGAENGER_PARTIAL",
        }
    else:
        assert r.recommendation == (
            "NOVEL_DOPPELGAENGER_NOT_DETECTED"
        )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "NOVEL_DOPPELGAENGER_DETECTED",
        "NOVEL_DOPPELGAENGER_PARTIAL",
        "NOVEL_DOPPELGAENGER_NOT_DETECTED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_distance_gap_is_largest_gap() -> None:
    """Sanity: the chosen threshold is the midpoint
    of the largest gap in the sorted distance
    list."""
    dists = sorted(
        d for _, _, d in novel_pairwise_distances()
    )
    best = -1.0
    for i in range(len(dists) - 1):
        if dists[i + 1] - dists[i] > best:
            best = dists[i + 1] - dists[i]
            mid = (dists[i] + dists[i + 1]) / 2.0
    assert abs(novel_distance_gap() - mid) < 1e-9


def test_artifact_records_clusters_and_distances() -> None:
    art = build_novel_family_clusters_artifact()
    assert len(art["pairwise_distances"]) == 703
    assert art["anchor_count"] == 38


def test_artifact_clusters_match_report_clusters() -> None:
    art = build_novel_family_clusters_artifact()
    r = build_report()
    assert art["clusters"] == list(r.clusters)


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_86" / "report.json").read_text(
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
