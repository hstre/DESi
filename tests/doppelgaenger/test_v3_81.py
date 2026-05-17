"""v3.81 — blind equivalence detection tests."""
from __future__ import annotations

import json
import pathlib

from desi.doppelgaenger.blind_cluster import (
    cluster_purity, cluster_recall,
    cluster_sizes, predicted_cluster_count,
)
from desi.doppelgaenger.equivalence import (
    all_blind_clusters, largest_gap_threshold,
    pairwise_distances, plateau_anchor_vectors,
)
from desi.doppelgaenger.report import (
    PURITY_THRESHOLD,
    build_blind_equivalence_clusters_artifact,
    build_report,
)
from desi.redundancy_masking.equivalence import (
    redundancy_classes,
)


def test_plateau_anchor_count_is_twenty() -> None:
    """The blind input is exactly the 20 plateau
    anchors, no coverage labels supplied."""
    assert len(plateau_anchor_vectors()) == 20


def test_pairwise_distance_count() -> None:
    """20 choose 2 = 190 pairs."""
    vecs = plateau_anchor_vectors()
    assert len(pairwise_distances(vecs)) == 190


def test_threshold_falls_in_largest_gap() -> None:
    """The data-driven threshold must lie in the
    largest jump of the sorted distance list, not
    at either extreme."""
    vecs = plateau_anchor_vectors()
    dists = pairwise_distances(vecs)
    thr = largest_gap_threshold(dists)
    sorted_d = sorted(d for _, _, d in dists)
    assert sorted_d[0] < thr < sorted_d[-1]


def test_blind_cluster_count_is_three() -> None:
    """Pflichtfrage 2: Entstehen genau 3 Cluster?"""
    assert predicted_cluster_count(
        all_blind_clusters(),
    ) == 3


def test_blind_cluster_sizes_are_eight_eight_four() -> None:
    """Pflichtfrage 3: Sind die Groessen korrekt
    (8/8/4)?"""
    sizes = cluster_sizes(all_blind_clusters())
    assert sorted(sizes, reverse=True) == [8, 8, 4]


def test_cluster_purity_is_one() -> None:
    """Killerfrage: blind clustering exactly
    matches the v3.79 redundancy classes."""
    purity = cluster_purity(
        all_blind_clusters(), redundancy_classes(),
    )
    assert purity == 1.0


def test_cluster_purity_meets_concept_gate() -> None:
    assert cluster_purity(
        all_blind_clusters(), redundancy_classes(),
    ) >= PURITY_THRESHOLD


def test_cluster_recall_is_one() -> None:
    assert cluster_recall(
        all_blind_clusters(), redundancy_classes(),
    ) == 1.0


def test_each_cluster_exactly_matches_a_class() -> None:
    r = build_report()
    matches = r.cluster_class_matches
    assert len(matches) == 3
    for m in matches:
        assert m["is_exact"] is True


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_detected_blind() -> None:
    assert build_report().recommendation == (
        "DOPPELGAENGER_DETECTED_BLIND"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DOPPELGAENGER_DETECTED_BLIND",
        "DOPPELGAENGER_HYPOTHESIS_WEAK",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_blind_clusters_match_redundancy_classes() -> None:
    """Every blind-cluster member set equals exactly
    one v3.79 redundancy class member set."""
    blind = {
        frozenset(c.members)
        for c in all_blind_clusters()
    }
    true = {
        frozenset(c.members)
        for c in redundancy_classes()
    }
    assert blind == true


def test_artifact_records_clusters_and_distances() -> None:
    art = build_blind_equivalence_clusters_artifact()
    assert len(art["clusters"]) == 3
    assert art["anchor_count"] == 20
    assert art["pairwise_distance_count"] == 190
    assert len(art["pairwise_distances"]) == 190


def test_artifact_threshold_matches_report() -> None:
    art = build_blind_equivalence_clusters_artifact()
    r = build_report()
    assert art["cluster_threshold"] == (
        r.cluster_threshold
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_81" / "report.json").read_text(
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
