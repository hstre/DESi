"""v3.33 — plateau resolution tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.epistemic_trajectory.state import StateVector
from desi.plateau_resolution.escalation import (
    apply_cause_specific_escalation,
    apply_extra_audit_stages,
)
from desi.plateau_resolution.hold_extension import (
    apply_extra_confidence_hold,
)
from desi.plateau_resolution.report import (
    MAX_NC_RESOLUTION_FP,
    build_failure_claims_artifact, build_report,
    build_resolution_artifact,
)
from desi.plateau_resolution.resolution import (
    StrategyKind, resolve_all_strategies, resolve_one,
)
from desi.support_plateau.extractor import (
    plateau_trajectory_ids,
)


def _sv(**overrides) -> StateVector:
    base = dict(
        frame_id=2.0, contradiction_load=0.0,
        anchor_density=0.5, source_quality=0.0,
        novelty=0.0, confidence=0.3, branch_cost=3.0,
        support_state=0.0, routing_state=2.0,
    )
    base.update(overrides)
    return StateVector(**base)


def test_strategy_kinds_match_directive() -> None:
    """Four closed strategies: A no_change,
    B extra_confidence_hold, C extra_audit_stages,
    D cause_specific."""
    assert {k.value for k in StrategyKind} == {
        "A_no_change", "B_extra_confidence_hold",
        "C_extra_audit_stages", "D_cause_specific",
    }


def test_strategy_a_is_identity() -> None:
    trajs = extract_all_trajectories()
    pids = set(plateau_trajectory_ids())
    for t in trajs:
        if t.trajectory_id not in pids:
            continue
        r = resolve_one(
            t, StrategyKind.STRATEGY_A_NO_CHANGE.value,
        )
        assert r.counterfactual_final_support == (
            t.states[-1].support_state
        )


def test_extra_confidence_hold_withdraws_audit() -> None:
    """+1 extra confidence_hold also withdraws the
    audit step on a plateau-shaped trajectory."""
    s0 = _sv(support_state=0.0)
    s1 = _sv(support_state=0.0, confidence=0.7)
    s2 = _sv(support_state=0.0)
    s3 = _sv(support_state=2.0)  # plateau
    out = apply_extra_confidence_hold((s0, s1, s2, s3))
    assert out[-1].support_state != 2.0


def test_extra_audit_stages_extends_trajectory() -> None:
    s0 = _sv(support_state=0.0)
    s1 = _sv(support_state=0.0)
    s2 = _sv(support_state=2.0)
    out = apply_extra_audit_stages((s0, s1, s2))
    assert len(out) == 5  # 3 + 2 extra anchors + final


def test_cause_specific_boosts_confidence_at_audit() -> None:
    s0 = _sv(support_state=0.0, confidence=0.7)
    s1 = _sv(support_state=0.0, confidence=0.7)
    s2 = _sv(support_state=2.0, confidence=0.2)
    out = apply_cause_specific_escalation((s0, s1, s2))
    # Boosted to max(0.7, 0.7, 0.2) = 0.7
    assert out[-1].confidence == 0.7
    # Above floor 0.5 -> re-audit lands at SUPPORTED
    assert out[-1].support_state == 4.0


def test_plateau_count_matches_v3_31() -> None:
    from desi.support_plateau.report import (
        build_report as v331,
    )
    assert (
        build_report().plateau_count
        == v331().metrics.plateau_count
    )


def test_nc_resolution_fp_meets_stop_rule() -> None:
    r = build_report()
    assert r.nc_resolution_fp_rate <= (
        MAX_NC_RESOLUTION_FP
    )
    assert not r.halt


def test_plateau_resolution_gain_positive() -> None:
    """Paper-10 gate #4: plateau_resolution_gain > 0."""
    assert build_report().plateau_resolution_gain > 0


def test_replay_stability_is_one() -> None:
    """Strategy outcomes must be deterministic across
    re-runs on the plateau set."""
    assert build_report().replay_stability >= 1.0


def test_strategy_b_resolves_more_than_a() -> None:
    """+1 extra confidence_hold must outperform the
    no-change baseline on the plateau set."""
    rep = build_report()
    by_strategy = {s.strategy: s for s in rep.strategy_results}
    assert (
        by_strategy["B_extra_confidence_hold"].resolved_count
        > by_strategy["A_no_change"].resolved_count
    )


def test_overcontrol_zero_on_plateau() -> None:
    """No strategy should demote a SUPPORTED trajectory
    on the plateau corpus (the plateau set is final at
    BRIDGE_REQUIRED, not SUPPORTED)."""
    rep = build_report()
    for s in rep.strategy_results:
        assert s.overcontrol == 0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PLATEAU_RESOLUTION_GAIN_POSITIVE",
        "PLATEAU_RESOLUTION_UNAVAILABLE",
        "PLATEAU_PHENOMENON_UNKNOWN",
        "HALT_NC_RESOLUTION_FP",
    }
    assert build_report().recommendation in allowed


def test_phenomenon_real_flag_set_consistently() -> None:
    r = build_report()
    # If we have plateau and a resolution gain, the
    # phenomenon flag should be True.
    if r.plateau_count >= 1 and r.plateau_resolution_gain > 0:
        assert r.plateau_phenomenon_real is True


def test_resolution_artifact_has_four_strategies_per_plateau() -> None:
    art = build_resolution_artifact()
    rep = build_report()
    expected = rep.plateau_count * 4
    assert len(art["outcomes"]) == expected


def test_failure_claims_artifact_has_one_claim_per_plateau() -> None:
    art = build_failure_claims_artifact()
    rep = build_report()
    assert art["claim_count"] == rep.plateau_count


def test_artifact_report_matches_live_build() -> None:
    """Stable fields pinned; smoothness means are
    volatile due to hash-seed-driven jitter."""
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_33" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    # Strategy results contain volatile smoothness means.
    art_meta = {
        k: v for k, v in art.items()
        if k != "strategy_results"
    }
    live_meta = {
        k: v for k, v in live.items()
        if k != "strategy_results"
    }
    assert art_meta == live_meta
    # Strategy results: stable per-strategy
    # resolved/unresolved/overcontrol counts.
    for a, l in zip(
        art["strategy_results"],
        live["strategy_results"],
    ):
        assert a["strategy"] == l["strategy"]
        assert a["resolved_count"] == l["resolved_count"]
        assert a["unresolved_count"] == l["unresolved_count"]
        assert a["overcontrol"] == l["overcontrol"]


def test_paper10_gate_all_pass() -> None:
    """Aggregate paper-10 gate check (mirrors
    paper10_go_no_go.md)."""
    from desi.plateau_causes.report import (
        build_report as v332,
    )
    from desi.support_plateau.report import (
        build_report as v331,
    )
    r31 = v331()
    r32 = v332()
    r33 = build_report()
    assert r31.metrics.plateau_count >= 20
    assert r31.metrics.plateau_replay_stability == 1.0
    assert r32.plateau_cluster_count >= 1
    assert r33.plateau_resolution_gain > 0
    assert r33.nc_resolution_fp_rate <= 0.10
