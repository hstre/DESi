"""v3.52 — semantic phase transition tests."""
from __future__ import annotations

import json
import pathlib

from desi.semantic_phase_transition.curve import (
    PhasePoint, compute_phase_curve,
    coupling_strength, discontinuity_score,
    saturation_point,
)
from desi.semantic_phase_transition.mass import (
    MASS_LEVELS, PROBE_RADIUS, SATURATION_MASS,
    all_mass_levels, first_k_ids,
    ordered_anchor_ids,
)
from desi.semantic_phase_transition.report import (
    build_report,
    build_semantic_phase_curve_artifact,
)


def test_mass_levels_match_directive() -> None:
    """Directive: 1, 2, 3, 4, 8 (plus k=0 baseline)."""
    assert MASS_LEVELS == (0, 1, 2, 3, 4, 8)


def test_saturation_mass_is_twenty() -> None:
    assert SATURATION_MASS == 20


def test_probe_radius_is_three_point_five() -> None:
    assert PROBE_RADIUS == 3.5


def test_ordered_anchor_ids_count() -> None:
    assert len(ordered_anchor_ids()) == 20


def test_ordered_anchor_ids_deterministic() -> None:
    a = ordered_anchor_ids()
    b = ordered_anchor_ids()
    assert a == b
    assert a == tuple(sorted(a))


def test_first_k_ids_clip() -> None:
    assert len(first_k_ids(8)) == 8
    assert len(first_k_ids(100)) == 20
    assert first_k_ids(0) == ()


def test_all_mass_levels_includes_saturation() -> None:
    assert all_mass_levels() == MASS_LEVELS + (
        SATURATION_MASS,
    )


def test_compute_phase_curve_length() -> None:
    curve = compute_phase_curve()
    assert len(curve) == len(all_mass_levels())


def test_phase_curve_monotonic_in_leakage() -> None:
    """Adding more anchors can only add more covered
    leakage trajectories (union-of-balls is
    monotone)."""
    curve = compute_phase_curve()
    leaks = [p.leakage_count for p in curve]
    assert leaks == sorted(leaks)


def test_plateau_recall_holds_at_one_from_k_one() -> None:
    """Every plateau anchor at distance <= 3.5 from
    every other plateau anchor: a single active
    anchor captures all 20."""
    curve = compute_phase_curve()
    for p in curve:
        if p.mass_level >= 1:
            assert p.plateau_recall == 1.0


def test_discontinuity_score_high() -> None:
    """Concept Gate #4: discontinuity_score > 0.
    Empirical: ~0.91 at r=3.5 (the k=3 -> k=4 jump
    accounts for 121 of the 133-leakage total)."""
    score = discontinuity_score(compute_phase_curve())
    assert score > 0
    assert score >= 0.5  # discrete phase


def test_saturation_point_is_four() -> None:
    """Empirical: smallest k where leakage = 133."""
    assert saturation_point(
        compute_phase_curve(),
    ) == 4


def test_coupling_strength_positive() -> None:
    """Overall subadditivity across the sweep."""
    coup = coupling_strength(compute_phase_curve())
    assert coup > 0
    assert coup >= 0.5


def test_replay_stability_is_one() -> None:
    """Concept Gate #5 surrogate."""
    assert build_report().replay_stability == 1.0


def test_phase_curve_jump_at_k_four() -> None:
    """Empirical: leakage_count jumps from 12 to 133
    between k=3 and k=4."""
    curve = compute_phase_curve()
    by_k = {p.mass_level: p.leakage_count for p in curve}
    assert by_k[3] == 12
    assert by_k[4] == 133


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PHASE_DISCRETE",
        "PHASE_PARTIAL_DISCONTINUITY",
        "PHASE_CONTINUOUS", "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_discrete() -> None:
    assert build_report().recommendation == (
        "PHASE_DISCRETE"
    )


def test_phase_curve_artifact_present() -> None:
    art = build_semantic_phase_curve_artifact()
    assert len(art["curve"]) == len(all_mass_levels())


def test_concept_gate_summary() -> None:
    """All five Semantic Field Probe Concept Gates
    evaluated end-to-end."""
    from desi.anti_anchor.report import (
        build_report as v351,
    )
    from desi.frame_artifact_audit.report import (
        build_report as v349,
    )
    from desi.pair_resonance.report import (
        build_report as v350,
    )
    r49 = v349()
    r50 = v350()
    r51 = v351()
    r52 = build_report()
    # Gate 1: radius_break survives frame masking
    assert r49.radius_break_survives_frame_masking is True
    # Gate 2: subadditivity_score > 0
    assert r50.plateau_summary.subadditivity_score > 0
    # Gate 3: anti_anchor_effect > 0
    assert r51.anti_anchor_effect > 0
    # Gate 4: discontinuity_score > 0
    assert r52.discontinuity_score > 0
    # Gate 5: replay_stability == 1.0 across sprints
    assert r49.replay_stability == 1.0
    assert r50.attribution_stability == 1.0
    assert r51.suppression_stability == 1.0
    assert r52.replay_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_52" / "report.json").read_text(
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
