"""v3.43 — leakage census tests."""
from __future__ import annotations

import json
import pathlib

from desi.field_leakage.census import (
    collect_leakage_cases, collect_leakage_trajectories,
    collect_plateau_anchors,
)
from desi.field_leakage.distance import (
    euclidean, manifold_distance,
    per_state_dim_overlap, trajectory_vector,
)
from desi.field_leakage.report import (
    build_leakage_inventory_artifact,
    build_manifold_distance_map_artifact, build_report,
)
from desi.support_plateau.extractor import (
    plateau_trajectory_ids,
)


def test_plateau_anchor_count_is_twenty() -> None:
    assert len(collect_plateau_anchors()) == 20


def test_leakage_count_is_one_hundred_forty_five() -> None:
    assert len(collect_leakage_trajectories()) == 145


def test_leakage_count_matches_v339_overcontrol() -> None:
    """v3.39 reports full_corpus_overcontrol = 145 for
    the frame_stability_condition selector; v3.43's
    leakage cohort is identical."""
    from desi.plateau_specificity_recovery.report import (
        build_report as v339,
    )
    assert build_report().leakage_count == (
        v339().full_corpus_overcontrol
    )


def test_no_leakage_id_overlaps_plateau() -> None:
    pids = set(plateau_trajectory_ids())
    leak_ids = {
        t.trajectory_id
        for t in collect_leakage_trajectories()
    }
    assert pids & leak_ids == set()


def test_manifold_distance_empty_returns_inf() -> None:
    d, idx = manifold_distance((0.0, 0.0), ())
    assert d == float("inf")
    assert idx == -1


def test_manifold_distance_picks_minimum() -> None:
    d, idx = manifold_distance(
        (0.0,), ((10.0,), (3.0,), (-5.0,)),
    )
    assert d == 3.0
    assert idx == 1


def test_per_state_dim_overlap_matches_attribute() -> None:
    p = collect_plateau_anchors()[0]
    l = collect_leakage_trajectories()[0]
    assert per_state_dim_overlap(
        p.states, l.states, "frame_id",
        len(p.states) - 2,
    ) is True  # both have frame_id=5.0 at index n-2
    assert per_state_dim_overlap(
        p.states, l.states, "support_state",
        len(p.states) - 1,
    ) is False  # plateau 2.0, leakage 4.0


def test_same_frame_family_rate_is_one() -> None:
    """All 145 leakages share the plateau frame
    anchor at index n-2; same_frame_family_rate = 1.0."""
    assert build_report().same_frame_family_rate == 1.0


def test_same_support_family_rate_is_one() -> None:
    """All 145 leakages share the plateau pre-audit
    support anchor (0.0) at index n-2."""
    assert build_report().same_support_family_rate == 1.0


def test_nearest_neighbor_rate_is_zero() -> None:
    """No leakage trajectory's nearest overall
    neighbour is a plateau case; the leakage cohort
    forms its own manifold."""
    assert build_report().nearest_neighbor_rate == 0.0


def test_explanation_replay_stability_is_one() -> None:
    """Paper-10 v4 gate #1: replay stability == 1.0."""
    assert build_report().explanation_replay_stability == 1.0


def test_recommendation_is_own_manifold() -> None:
    assert build_report().recommendation == (
        "LEAKAGE_FORMS_OWN_MANIFOLD"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "LEAKAGE_FORMS_OWN_MANIFOLD",
        "LEAKAGE_BORDERS_PLATEAU",
        "HALT_EXPLANATION_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_mean_manifold_distance_within_observed_range() -> None:
    r = build_report()
    assert (
        r.min_manifold_distance
        <= r.mean_manifold_distance
        <= r.max_manifold_distance
    )


def test_leakage_cluster_count_is_three() -> None:
    """Empirical: the 145 leakages form three 1-NN
    sub-clusters (sizes 121, 12, 12)."""
    r = build_report()
    assert r.leakage_cluster_count == 3
    assert r.largest_cluster_size == 121


def test_reason_distribution_closed() -> None:
    allowed = {
        "FRAME_FAMILY_AUDIT_WITHDRAWN",
        "NON_FRAME_AUDIT_WITHDRAWN",
    }
    assert set(
        build_report().reason_distribution.keys()
    ) <= allowed


def test_all_leakage_marked_frame_family() -> None:
    cases = collect_leakage_cases()
    assert all(
        c.machine_readable_reason
        == "FRAME_FAMILY_AUDIT_WITHDRAWN"
        for c in cases
    )


def test_leakage_inventory_artifact_count_matches() -> None:
    art = build_leakage_inventory_artifact()
    assert art["case_count"] == 145
    assert len(art["cases"]) == 145


def test_distance_map_artifact_dimensions() -> None:
    art = build_manifold_distance_map_artifact()
    assert len(art["plateau_anchors"]) == 20
    assert len(art["rows"]) == 145
    for row in art["rows"][:3]:
        assert len(row["distances"]) == 20


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_43" / "report.json").read_text(
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
