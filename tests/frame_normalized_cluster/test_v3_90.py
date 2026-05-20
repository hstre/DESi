"""v3.90 — frame-normalized clustering tests."""
from __future__ import annotations

import json
import pathlib

from desi.frame_normalized_cluster.cluster import (
    all_normalized_clusters,
    normalized_cluster_count,
    normalized_cluster_purity,
    normalized_cluster_recall,
    normalized_cluster_sizes,
    normalized_distance_gap,
    normalized_pairwise_distances,
)
from desi.frame_normalized_cluster.normalize import (
    frame_normalized_vectors,
)
from desi.frame_normalized_cluster.report import (
    PURITY_THRESHOLD,
    build_frame_normalized_clusters_artifact,
    build_report,
)


def test_normalized_vector_count_is_thirty_eight() -> None:
    assert len(frame_normalized_vectors()) == 38


def test_pairwise_distance_count() -> None:
    assert len(normalized_pairwise_distances()) == 703


def test_normalized_distance_gap_in_data_range() -> None:
    dists = sorted(
        d for _, _, d in normalized_pairwise_distances()
    )
    gap = normalized_distance_gap()
    assert dists[0] < gap < dists[-1]


def test_clusters_partition_all_anchors() -> None:
    cls = all_normalized_clusters()
    total = sum(len(c.members) for c in cls)
    assert total == 38


def test_normalized_purity_beats_baseline() -> None:
    """Killerfrage: Doppelganger-Geometrie kehrt
    teilweise zurueck nach Frame-Normalisierung."""
    from desi.novel_family_cluster.cluster import (
        cluster_purity,
        all_novel_blind_clusters,
    )
    base = cluster_purity(all_novel_blind_clusters())
    assert normalized_cluster_purity() > base


def test_normalized_purity_in_unit_interval() -> None:
    assert (
        0.0
        <= normalized_cluster_purity()
        <= 1.0
    )


def test_normalized_recall_in_unit_interval() -> None:
    assert (
        0.0
        <= normalized_cluster_recall()
        <= 1.0
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DOPPELGAENGER_RECOVERED",
        "DOPPELGAENGER_PARTIAL_RECOVERY",
        "DOPPELGAENGER_WEAK_RECOVERY",
        "DOPPELGAENGER_NOT_RECOVERED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_consistent_with_purity() -> None:
    r = build_report()
    if r.normalized_cluster_purity >= PURITY_THRESHOLD:
        assert r.recommendation in {
            "DOPPELGAENGER_RECOVERED",
            "DOPPELGAENGER_PARTIAL_RECOVERY",
        }
    elif r.purity_delta > 0:
        assert r.recommendation == (
            "DOPPELGAENGER_WEAK_RECOVERY"
        )
    else:
        assert r.recommendation == (
            "DOPPELGAENGER_NOT_RECOVERED"
        )


def test_purity_delta_matches_difference() -> None:
    r = build_report()
    assert r.purity_delta == round(
        r.normalized_cluster_purity
        - r.baseline_purity,
        6,
    )


def test_artifact_records_clusters_and_distances() -> None:
    art = build_frame_normalized_clusters_artifact()
    assert art["pairwise_distance_count"] == 703
    assert art["normalized_cluster_count"] == (
        normalized_cluster_count()
    )


def test_normalized_clustering_recovers_pure_subclusters() -> None:
    """At least one cluster must be pure (every
    member shares a family). v3.90 should expose
    some doppelganger structure."""
    from desi.novel_families import (
        all_family_members,
    )
    fam = {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }
    any_pure = False
    for c in all_normalized_clusters():
        families = {fam[m] for m in c.members}
        if len(families) == 1 and len(c.members) > 1:
            any_pure = True
            break
    assert any_pure


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_90" / "report.json").read_text(
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
