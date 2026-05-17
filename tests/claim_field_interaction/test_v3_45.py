"""v3.45 — claim-field interaction tests."""
from __future__ import annotations

import json
import pathlib

from desi.claim_field_interaction.attribution import (
    dominant_anchors, per_anchor_leakage,
)
from desi.claim_field_interaction.interaction import (
    InterferenceFinding, MassOutcome,
    interference_findings, run_all_masses, run_at_mass,
)
from desi.claim_field_interaction.mass import (
    MASS_LEVELS, PROBE_RADIUS, SATURATION_MASS,
    active_anchor_subset, active_anchor_vectors,
    ordered_plateau_anchors,
)
from desi.claim_field_interaction.report import (
    build_claim_field_effects_artifact,
    build_field_leakage_claims_artifact, build_report,
)


def test_mass_levels_match_directive() -> None:
    """Directive: 0, 1, 2, 4, 8."""
    assert MASS_LEVELS == (0, 1, 2, 4, 8)


def test_saturation_mass_is_twenty() -> None:
    assert SATURATION_MASS == 20


def test_probe_radius_is_four() -> None:
    """Smallest radius from v3.44 closed set that
    exposes the leakage cohort."""
    assert PROBE_RADIUS == 4.0


def test_anchor_ordering_is_deterministic() -> None:
    a = [t.trajectory_id for t in ordered_plateau_anchors()]
    b = [t.trajectory_id for t in ordered_plateau_anchors()]
    assert a == b
    assert a == sorted(a)


def test_active_anchor_subset_zero_is_empty() -> None:
    assert active_anchor_subset(0) == ()


def test_active_anchor_subset_negative_is_empty() -> None:
    assert active_anchor_subset(-1) == ()


def test_active_anchor_subset_clips_at_population() -> None:
    """Asking for more anchors than exist returns the
    full set, not a fail."""
    assert len(active_anchor_subset(1000)) == len(
        ordered_plateau_anchors(),
    )


def test_run_at_mass_zero_never_fires() -> None:
    outs = run_at_mass(0)
    assert all(not o.selector_fired for o in outs)
    assert all(o.leakage is False for o in outs)
    assert all(o.plateau_resolved is False for o in outs)


def test_run_at_mass_full_matches_v344_inf() -> None:
    """Mass=20 with probe_radius=4.0 ≡ v3.44 r=4.0 on
    the full corpus: same set of (resolved, leakage)
    outcomes."""
    from desi.field_radius_sweep.ablation import (
        run_at_radius,
    )
    a = {
        (o.trajectory_id, o.plateau_resolved, o.leakage)
        for o in run_at_mass(20)
    }
    b = {
        (o.trajectory_id, o.plateau_resolved, o.leakage)
        for o in run_at_radius(4.0)
    }
    assert a == b


def test_mass_effect_curve_monotone_in_leakage() -> None:
    r = build_report()
    leaks = [
        p["leakage_count"] for p in r.mass_effect_curve
    ]
    assert leaks == sorted(leaks)


def test_single_anchor_captures_121_leakages() -> None:
    """At k=1 (the first plateau anchor, v23:R4_04),
    121 leakages fall within the probe ball."""
    r = build_report()
    k1 = next(
        p for p in r.mass_effect_curve
        if p["mass_level"] == 1
    )
    assert k1["leakage_count"] == 121


def test_saturation_at_k_two() -> None:
    """Two anchors are sufficient to cover all 145
    leakages at probe_radius=4.0."""
    assert build_report().leakage_saturation == 2


def test_interference_exists_no_repulsion() -> None:
    r = build_report()
    assert r.interference_count > 0
    assert r.repulsion_count == 0


def test_attribution_stability_meets_gate() -> None:
    """Paper-10 v4 gate #5: attribution_stability == 1.0."""
    assert build_report().attribution_stability == 1.0


def test_dominant_mass_claims_length() -> None:
    assert len(build_report().dominant_mass_claims) == 5


def test_per_anchor_leakage_count_matches_population() -> None:
    """One contribution per plateau anchor."""
    assert len(per_anchor_leakage()) == 20


def test_per_anchor_leakage_bounded() -> None:
    for c in per_anchor_leakage():
        assert 0 <= c.leakage_count <= 145


def test_dominant_anchors_break_ties_alphabetically() -> None:
    contribs = per_anchor_leakage()
    top5 = dominant_anchors(contribs)
    # When multiple anchors tie at 145, alphabetical
    # tie-break means the lexicographically smallest
    # ids appear first.
    full_coverers = sorted(
        c.anchor_id for c in contribs
        if c.leakage_count == 145
    )
    # Top entries should be these alphabetically
    # smallest full-coverers
    if len(full_coverers) >= 5:
        assert list(top5) == full_coverers[:5]


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MASS_FIELD_ADDITIVE",
        "MASS_FIELD_INTERACTS",
        "MASS_NO_SATURATION",
        "HALT_ATTRIBUTION_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_interacts() -> None:
    """interference_count > 0 → MASS_FIELD_INTERACTS."""
    assert build_report().recommendation == (
        "MASS_FIELD_INTERACTS"
    )


def test_claim_field_effects_artifact_outcomes_count() -> None:
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    art = build_claim_field_effects_artifact()
    expected = (
        len(MASS_LEVELS) + 1  # the saturation mass too
    ) * len(list(extract_all_trajectories()))
    assert len(art["outcomes"]) == expected


def test_field_leakage_claims_artifact_count() -> None:
    art = build_field_leakage_claims_artifact()
    assert art["claim_count"] == 145
    assert len(art["claims"]) == 145


def test_paper10_v4_gate_summary() -> None:
    """All five Paper-10 v4 gates evaluated end-to-end."""
    from desi.field_leakage.report import (
        build_report as v343,
    )
    from desi.field_radius_sweep.report import (
        MIN_LEAKAGE_REDUCTION,
        build_report as v344,
    )
    r43 = v343()
    r44 = v344()
    r45 = build_report()
    # Gate 1
    assert r43.explanation_replay_stability == 1.0
    # Gate 2
    assert r44.optimal_radius is not None
    # Gate 3
    assert r44.optimal_plateau_recall >= 0.90
    # Gate 4
    assert r44.optimal_leakage_reduction >= (
        MIN_LEAKAGE_REDUCTION
    )
    # Gate 5
    assert r45.attribution_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_45" / "report.json").read_text(
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
