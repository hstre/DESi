"""v3.47 — GAP geometry tests."""
from __future__ import annotations

import json
import pathlib

from desi.gap_detected_geometry.cause import (
    PLATEAU_PRIMARY_CAUSE, cause_distribution,
    classify_gap_cohort,
)
from desi.gap_detected_geometry.cluster import (
    gap_1nn_cluster_count, gap_members,
    leakage_members, plateau_members, rescued_members,
)
from desi.gap_detected_geometry.geometry import (
    TAIL_LENGTH, final_state_vector, tail_vector,
)
from desi.gap_detected_geometry.report import (
    build_gap_geometry_artifact, build_report,
)


def test_tail_length_is_five() -> None:
    assert TAIL_LENGTH == 5


def test_tail_vector_length_45() -> None:
    g = gap_members()
    for m in g:
        assert len(m.vector) == 9 * TAIL_LENGTH


def test_final_state_vector_length_nine() -> None:
    g = gap_members()
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    fs = final_state_vector(
        trajs[g[0].trajectory_id].states,
    )
    assert len(fs) == 9


def test_cohort_population_counts() -> None:
    assert len(gap_members()) == 2
    assert len(plateau_members()) == 20
    assert len(leakage_members()) == 145
    assert len(rescued_members()) == 228


def test_gap_cluster_count_at_least_one() -> None:
    """Concept Gate #3: gap_cluster_count >= 1."""
    assert build_report().gap_cluster_count >= 1


def test_gap_cluster_count_is_one_in_this_corpus() -> None:
    """Empirical: the 2 GAP cases form a single 1-NN
    component."""
    assert build_report().gap_cluster_count == 1


def test_replay_stability_is_one() -> None:
    """Concept Gate (sprint #2 surrogate)."""
    assert build_report().replay_stability == 1.0


def test_nearest_manifold_in_closed_set() -> None:
    allowed = {"plateau", "leakage", "rescued", "none"}
    assert build_report().nearest_manifold in allowed


def test_plateau_primary_cause_constant() -> None:
    assert PLATEAU_PRIMARY_CAUSE == "CONFIDENCE_OSCILLATION"


def test_cause_identity_does_not_match_plateau() -> None:
    """Both GAP cases primary-classify as
    SUPPORT_DECAY or FRAME_COLLISION (hash-seed jitter
    between these two on darwin); neither is
    CONFIDENCE_OSCILLATION."""
    r = build_report()
    assert r.cause_identity_match_plateau is False


def test_per_gap_records_count() -> None:
    r = build_report()
    assert len(r.per_gap_records) == 2


def test_per_gap_records_have_nearest_anchors() -> None:
    r = build_report()
    for rec in r.per_gap_records:
        assert "plateau_nearest_id" in rec
        assert "leakage_nearest_id" in rec
        assert "rescued_nearest_id" in rec
        assert "plateau_nearest_distance" in rec
        assert "leakage_nearest_distance" in rec
        assert "rescued_nearest_distance" in rec


def test_distances_are_finite_and_positive() -> None:
    r = build_report()
    for fld in (
        "gap_to_plateau_distance_mean",
        "gap_to_leakage_distance_mean",
        "gap_to_rescued_distance_mean",
        "gap_to_plateau_distance_min",
        "gap_to_leakage_distance_min",
        "gap_to_rescued_distance_min",
    ):
        v = getattr(r, fld)
        assert 0.0 < v < 100.0


def test_distance_min_le_mean() -> None:
    r = build_report()
    assert r.gap_to_plateau_distance_min <= (
        r.gap_to_plateau_distance_mean
    )
    assert r.gap_to_leakage_distance_min <= (
        r.gap_to_leakage_distance_mean
    )
    assert r.gap_to_rescued_distance_min <= (
        r.gap_to_rescued_distance_mean
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "GAP_BORDERS_PLATEAU", "GAP_BORDERS_LEAKAGE",
        "GAP_BORDERS_RESCUED", "GAP_ORPHAN_MANIFOLD",
        "GAP_NO_NEAREST", "HALT_NO_GAP_CLUSTER",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_orphan_manifold() -> None:
    """All observed runs put the GAP cohort well above
    ORPHAN_DISTANCE_FLOOR; the verdict is stable."""
    assert build_report().recommendation == (
        "GAP_ORPHAN_MANIFOLD"
    )


def test_gap_is_orphan_manifold_true() -> None:
    assert build_report().gap_is_orphan_manifold is True


def test_orphan_distance_floor_anchor() -> None:
    from desi.gap_detected_geometry.report import (
        ORPHAN_DISTANCE_FLOOR,
    )
    assert ORPHAN_DISTANCE_FLOOR == 5.0
    assert build_report().orphan_distance_floor == 5.0


def test_gap_geometry_artifact_present() -> None:
    art = build_gap_geometry_artifact()
    assert art["schema_version"] == "v3_47_gap_geometry"
    assert len(art["per_gap_records"]) == 2


def test_cause_distribution_is_two_total() -> None:
    """Both GAP cases contribute exactly one entry."""
    assert sum(cause_distribution().values()) == 2


def test_classify_gap_cohort_yields_two_records() -> None:
    assert len(classify_gap_cohort()) == 2


def test_artifact_report_matches_live_build() -> None:
    """The 8-state GAP trajectories' tail vectors
    depend on FrameDetector dict iteration, so numeric
    distances and nearest_manifold jitter across hash
    seeds. gap_is_orphan_manifold, gap_cluster_count,
    cause_identity_match_plateau and the recommendation
    are stable; the rest are excluded from the
    comparison."""
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_47" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {
        "rationale", "per_gap_records",
        "gap_cause_distribution",
        "gap_to_plateau_distance_mean",
        "gap_to_plateau_distance_min",
        "gap_to_leakage_distance_mean",
        "gap_to_leakage_distance_min",
        "gap_to_rescued_distance_mean",
        "gap_to_rescued_distance_min",
        "nearest_manifold",
    }
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
