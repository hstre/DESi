"""v3.36 — noise + timing tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.plateau_noise_timing.noise import (
    NOISE_LEVELS, apply_noise, run_noise_level,
    simulate_reaudit,
)
from desi.plateau_noise_timing.report import (
    MIN_NOISE_STABILITY, MIN_TIMING_SENSITIVITY,
    build_noise_artifact, build_report,
    build_timing_artifact,
)
from desi.plateau_noise_timing.timing import (
    TimingPoint, apply_timed_hold, run_timing,
)
from desi.support_plateau.extractor import (
    plateau_trajectory_ids,
)


def test_noise_levels_match_directive() -> None:
    """Directive: -20%, -10%, -5%, +5%, +10%, +20%."""
    expected = {-0.20, -0.10, -0.05, 0.05, 0.10, 0.20}
    assert set(NOISE_LEVELS) == expected


def test_timing_points_match_directive() -> None:
    expected = {
        "t_minus_1", "t_minus_2", "t_minus_3",
        "after_audit",
    }
    assert {k.value for k in TimingPoint} == expected


def test_simulate_reaudit_thresholds() -> None:
    from desi.epistemic_trajectory.state import StateVector
    def _sv(c):
        return StateVector(
            frame_id=2.0, contradiction_load=0.0,
            anchor_density=0.5, source_quality=0.0,
            novelty=0.0, confidence=c,
            branch_cost=3.0, support_state=0.0,
            routing_state=2.0,
        )
    # High confidence -> SUPPORTED
    assert simulate_reaudit((_sv(0.7),)) == 4.0
    # Mid confidence -> BRIDGE_REQUIRED
    assert simulate_reaudit((_sv(0.3),)) == 2.0
    # Very low confidence -> REJECTED
    assert simulate_reaudit((_sv(0.05),)) == 3.0


def test_apply_noise_scales_confidence() -> None:
    from desi.epistemic_trajectory.state import StateVector
    s = StateVector(
        frame_id=2.0, contradiction_load=0.0,
        anchor_density=0.5, source_quality=0.0,
        novelty=0.0, confidence=0.5, branch_cost=3.0,
        support_state=0.0, routing_state=2.0,
    )
    noisy = apply_noise((s,), 0.10)
    assert noisy[0].confidence == 0.55
    noisy = apply_noise((s,), -0.20)
    assert noisy[0].confidence == 0.4


def test_noise_stability_meets_gate() -> None:
    """Paper-10 v2 gate #3: noise_stability >= 0.80."""
    assert build_report().noise_stability >= (
        MIN_NOISE_STABILITY
    )


def test_timing_sensitivity_meets_gate() -> None:
    """Paper-10 v2 gate #4: timing_sensitivity > 0."""
    assert build_report().timing_sensitivity >= (
        MIN_TIMING_SENSITIVITY
    )


def test_replay_stability_is_one() -> None:
    """Paper-10 v2 gate #5: replay_stability == 1.0."""
    assert build_report().replay_stability == 1.0


def test_pre_audit_timings_resolve_all_plateaus() -> None:
    """All pre-audit timing points (t-1, t-2, t-3)
    resolve every plateau via audit withdrawal."""
    rep = build_report()
    pc = rep.plateau_count
    assert rep.timing_resolution_counts[
        "t_minus_1"
    ] == pc
    assert rep.timing_resolution_counts[
        "t_minus_2"
    ] == pc
    assert rep.timing_resolution_counts[
        "t_minus_3"
    ] == pc


def test_after_audit_timing_resolves_nothing() -> None:
    """The after_audit timing point cannot rescue: the
    audit has already committed and the holding action
    has no pre-audit window to clamp."""
    assert build_report().timing_resolution_counts[
        "after_audit"
    ] == 0


def test_no_breakpoints_in_current_corpus() -> None:
    """Under +/- 20% confidence noise, every plateau
    trajectory in the v3 corpus stays at
    BRIDGE_REQUIRED. plateau_breakpoints is empty."""
    assert build_report().plateau_breakpoints == ()


def test_noise_artifact_records_all_combinations() -> None:
    art = build_noise_artifact()
    rep = build_report()
    expected = rep.plateau_count * len(NOISE_LEVELS)
    assert len(art["outcomes"]) == expected


def test_timing_artifact_records_all_combinations() -> None:
    art = build_timing_artifact()
    rep = build_report()
    expected = rep.plateau_count * len(TimingPoint)
    assert len(art["outcomes"]) == expected


def test_validation_claims_artifact_present() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    doc = json.loads(
        (root / "artifacts" / "v3_36"
         / "plateau_validation_claims.json").read_text(
            encoding="utf-8",
        )
    )
    assert doc["claim_count"] >= 1


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PLATEAU_HOLDS_UNDER_NOISE_AND_TIMING",
        "PLATEAU_INCONCLUSIVE",
        "HALT_LOW_NOISE_STABILITY",
    }
    assert build_report().recommendation in allowed


def test_artifact_report_matches_live_build() -> None:
    """Numeric fields are stable; rationale text can
    drift on dict-iteration ordering. Compare stable
    fields exactly; tolerate rationale."""
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_36" / "report.json").read_text(
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


def test_paper10_v2_gate_summary() -> None:
    """Aggregate check matching paper10_go_no_go_v2.md.
    Four of five gates pass; specificity (v3.35) fails."""
    from desi.plateau_cross_transfer.report import (
        build_report as v335,
    )
    from desi.plateau_hold_sweep.report import (
        build_report as v334,
    )
    r34 = v334()
    r35 = v335()
    r36 = build_report()
    # Gate 1: minimal_effective_hold == 1
    assert r34.curves.minimal_effective_hold == 1
    # Gate 2: specificity_score >= 0.80 — empirically
    # fails on this corpus.
    assert r35.specificity_score < 0.80
    # Gate 3: noise_stability >= 0.80
    assert r36.noise_stability >= 0.80
    # Gate 4: timing_sensitivity > 0
    assert r36.timing_sensitivity > 0
    # Gate 5: replay_stability == 1.0
    assert r36.replay_stability == 1.0
