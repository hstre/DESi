"""v3.44 — radius-sweep tests."""
from __future__ import annotations

import json
import math
import pathlib

from desi.field_leakage.census import collect_plateau_anchors
from desi.field_leakage.distance import trajectory_vector
from desi.field_radius_sweep.ablation import (
    RadiusOutcome, run_all_radii, run_at_radius,
)
from desi.field_radius_sweep.curve import (
    MIN_PLATEAU_RECALL, RadiusPoint, compute_curve,
    pick_largest_clean_radius, pick_optimal_radius,
)
from desi.field_radius_sweep.radius import (
    RADII, radius_label, selector_for_radius,
)
from desi.field_radius_sweep.report import (
    MIN_LEAKAGE_REDUCTION, build_radius_sweep_artifact,
    build_report,
)
from desi.support_plateau.extractor import (
    plateau_trajectory_ids,
)


def test_radii_match_directive() -> None:
    """Directive: 0.25, 0.5, 1.0, 2.0, 4.0, ∞."""
    assert RADII == (
        0.25, 0.5, 1.0, 2.0, 4.0, math.inf,
    )


def test_radius_label_finite_and_infinite() -> None:
    assert radius_label(0.25) == "0.25"
    assert radius_label(math.inf) == "inf"


def test_selector_negative_radius_never_fires() -> None:
    plats = collect_plateau_anchors()
    plat_vecs = tuple(
        trajectory_vector(t.states) for t in plats
    )
    assert selector_for_radius(
        plats[0].states, -1.0, plat_vecs,
    ) is False


def test_selector_inf_radius_always_fires_on_plateau() -> None:
    plats = collect_plateau_anchors()
    plat_vecs = tuple(
        trajectory_vector(t.states) for t in plats
    )
    for t in plats:
        assert selector_for_radius(
            t.states, math.inf, plat_vecs,
        ) is True


def test_plateau_self_distance_is_zero() -> None:
    """Smallest radius (0.25) still fires on every
    plateau trajectory because the plateau anchor set
    contains its own vector."""
    plats = collect_plateau_anchors()
    plat_vecs = tuple(
        trajectory_vector(t.states) for t in plats
    )
    for t in plats:
        assert selector_for_radius(
            t.states, 0.25, plat_vecs,
        ) is True


def test_run_at_radius_covers_corpus() -> None:
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    outs = run_at_radius(math.inf)
    assert len(outs) == len(
        list(extract_all_trajectories()),
    )


def test_recall_is_one_for_every_radius() -> None:
    """The plateau set is in its own manifold (distance
    zero), so every radius >= 0 fires on every plateau
    trajectory and resolves all 20."""
    r = build_report()
    for entry in r.recall_curve:
        assert entry["plateau_recall"] == 1.0


def test_leakage_curve_step_function() -> None:
    """Empirical: leakage is 0 for r <= 2.0 and 145 for
    r >= 4.0 (the leakage cohort sits ~3.0 units from
    the plateau manifold)."""
    r = build_report()
    by_lbl = {
        e["radius_label"]: e["leakage_count"]
        for e in r.leakage_curve
    }
    assert by_lbl["0.25"] == 0
    assert by_lbl["0.5"] == 0
    assert by_lbl["1"] == 0
    assert by_lbl["2"] == 0
    assert by_lbl["4"] == 145
    assert by_lbl["inf"] == 145


def test_pick_optimal_radius_returns_smallest_clean() -> None:
    """All four small radii give zero leakage; the
    optimum is the smallest of them."""
    assert build_report().optimal_radius == "0.25"


def test_pick_largest_clean_radius_returns_two() -> None:
    """Among the clean radii, the largest is 2.0."""
    assert build_report().largest_clean_radius == "2"


def test_optimal_leakage_reduction_is_one() -> None:
    """Paper-10 v4 gate #4: leakage_reduction >= 0.90."""
    r = build_report()
    assert r.optimal_leakage_reduction >= MIN_LEAKAGE_REDUCTION
    assert r.optimal_leakage_reduction == 1.0


def test_optimal_plateau_recall_meets_gate() -> None:
    """Paper-10 v4 gate #3: plateau_recall >= 0.90."""
    assert build_report().optimal_plateau_recall >= (
        MIN_PLATEAU_RECALL
    )


def test_radius_stability_is_one() -> None:
    """Paper-10 v4 gate #5 surrogate: replay
    determinism over the radius sweep."""
    assert build_report().radius_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "FIELD_RADIUS_RECOVERED", "FIELD_RADIUS_PARTIAL",
        "HALT_NO_OPTIMAL_RADIUS",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_recovered() -> None:
    assert build_report().recommendation == (
        "FIELD_RADIUS_RECOVERED"
    )


def test_compute_curve_matches_radii_count() -> None:
    pids = plateau_trajectory_ids()
    points = compute_curve(run_all_radii(), len(pids))
    assert len(points) == len(RADII)


def test_radius_sweep_artifact_counts() -> None:
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    art = build_radius_sweep_artifact()
    assert len(art["radii"]) == len(RADII)
    assert len(art["curve"]) == len(RADII)
    expected = len(RADII) * len(
        list(extract_all_trajectories()),
    )
    assert len(art["outcomes"]) == expected


def test_pick_optimal_handles_empty_eligible_set() -> None:
    """If every radius gives non-zero leakage, the
    optimum is None and the sprint halts per directive."""
    curve = (
        RadiusPoint(
            radius=0.25, radius_label="0.25",
            plateau_resolved_count=20,
            leakage_count=10, plateau_recall=1.0,
            leakage_reduction=0.0,
        ),
    )
    assert pick_optimal_radius(curve) is None
    assert pick_largest_clean_radius(curve) is None


def test_radii_tested_is_six() -> None:
    assert build_report().radii_tested == 6


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_44" / "report.json").read_text(
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
