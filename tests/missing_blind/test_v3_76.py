"""v3.76 — blind recovery tests."""
from __future__ import annotations

import json
import pathlib

from desi.missing_blind.blind import (
    CLUSTER_DISTANCE_THRESHOLD, HIDDEN_ROLES,
    HIDDEN_SUBSET, cluster_orphans,
    orphan_indices, visible_set,
)
from desi.missing_blind.recover import (
    CLUSTER_SIZE_BRIDGE_CEILING,
    assign_clusters, false_reconstruction_rate,
    missing_count_error,
    predicted_distinct_regions,
    region_recall, role_recall,
)
from desi.missing_blind.report import (
    NEPTUN_REGION_RECALL_FLOOR,
    build_blind_recovery_artifact, build_report,
)


def test_cluster_threshold_anchor() -> None:
    assert CLUSTER_DISTANCE_THRESHOLD == 1.0


def test_cluster_size_bridge_ceiling_anchor() -> None:
    assert CLUSTER_SIZE_BRIDGE_CEILING == 50


def test_neptun_region_recall_floor() -> None:
    assert NEPTUN_REGION_RECALL_FLOOR == 0.70


def test_hidden_subset_three_anchors() -> None:
    assert len(HIDDEN_SUBSET) == 3
    assert set(HIDDEN_SUBSET) == {
        "v23:R5_02", "v23:R5_04", "v314:D02",
    }


def test_hidden_roles_complete() -> None:
    assert set(HIDDEN_ROLES.keys()) == set(
        HIDDEN_SUBSET,
    )


def test_visible_set_is_only_low() -> None:
    """All but LOW are hidden."""
    assert visible_set() == ("v23:R4_04",)


def test_orphan_count_is_133() -> None:
    """Hiding HIGH + REDUNDANT + BRIDGE leaves only
    LOW (coverage 0), so all 133 covered leakages
    become orphans."""
    assert len(orphan_indices()) == 133


def test_cluster_count_is_two() -> None:
    """Single-link clustering at threshold 1.0
    separates the 12-leakage and 121-leakage
    regions."""
    assert len(cluster_orphans()) == 2


def test_cluster_sizes() -> None:
    sizes = sorted(
        len(c.member_indices)
        for c in cluster_orphans()
    )
    assert sizes == [12, 121]


def test_assignments_count() -> None:
    assert len(assign_clusters()) == 2


def test_both_clusters_correctly_matched() -> None:
    for a in assign_clusters():
        assert a.correctly_matched is True


def test_bridge_cluster_predicted_correctly() -> None:
    assignments = assign_clusters()
    bridge_assignment = next(
        a for a in assignments
        if a.cluster_size <= (
            CLUSTER_SIZE_BRIDGE_CEILING
        )
    )
    assert bridge_assignment.predicted_role == "bridge"
    assert bridge_assignment.nearest_hidden_id == (
        "v23:R5_02"
    )


def test_high_cluster_predicted_correctly() -> None:
    assignments = assign_clusters()
    large = next(
        a for a in assignments
        if a.cluster_size > (
            CLUSTER_SIZE_BRIDGE_CEILING
        )
    )
    assert large.predicted_role == (
        "high_or_redundant"
    )
    assert large.nearest_hidden_id in {
        "v23:R5_04", "v314:D02",
    }


def test_missing_count_error_is_zero() -> None:
    """2 predicted distinct regions matches 2 actual
    distinct regions (HIGH+REDUNDANT share coverage)."""
    assert build_report().missing_count_error == 0


def test_region_recall_meets_gate() -> None:
    """Neptun concept gate #4: region_recall >= 0.70."""
    assert build_report().region_recall >= (
        NEPTUN_REGION_RECALL_FLOOR
    )


def test_region_recall_is_perfect() -> None:
    assert build_report().region_recall == 1.0


def test_role_recall_is_perfect() -> None:
    assert build_report().role_recall == 1.0


def test_false_reconstruction_rate_is_zero() -> None:
    assert build_report().false_reconstruction_rate == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_usable() -> None:
    assert build_report().recommendation == (
        "BLIND_RECOVERY_USABLE"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "BLIND_RECOVERY_USABLE",
        "BLIND_RECOVERY_WEAK",
        "BLIND_RECOVERY_FAILED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_assignments() -> None:
    art = build_blind_recovery_artifact()
    assert len(art["cluster_assignments"]) == 2
    assert art["hidden_subset"] == list(
        HIDDEN_SUBSET,
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_76" / "report.json").read_text(
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
