"""v3.48 — GAP resolution strategy tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.epistemic_trajectory.state import StateVector
from desi.gap_detected.state import GAP_DETECTED_STATE
from desi.gap_detected_resolution.resolution import (
    resolve_all_strategies_on_gaps, resolve_on_corpus,
)
from desi.gap_detected_resolution.report import (
    build_gap_resolution_artifact, build_report,
    build_terminal_gap_claims_artifact,
)
from desi.gap_detected_resolution.strategies import (
    StrategyKind, apply_strategy, strategy_a,
    strategy_b, strategy_c, strategy_d, strategy_e,
    strategy_f, strategy_g,
)


def _sv(support: float, anchor: float = 0.0) -> StateVector:
    return StateVector(
        frame_id=0.0, contradiction_load=0.0,
        anchor_density=anchor, source_quality=0.0,
        novelty=0.0, confidence=0.5, branch_cost=1.0,
        support_state=support, routing_state=0.0,
    )


def test_strategy_kinds_match_directive() -> None:
    expected = {
        "A_no_change", "B_confidence_hold",
        "C_audit_delay", "D_bridge_expansion",
        "E_premise_re_extraction", "F_frame_replay",
        "G_bridge_and_premise",
    }
    assert {k.value for k in StrategyKind} == expected


def test_strategy_a_is_identity() -> None:
    s = (_sv(4.0), _sv(1.0))
    assert strategy_a(s) == s


def test_strategy_d_only_fires_on_gap() -> None:
    """D should not touch a SUPPORTED-ending
    trajectory."""
    s = (_sv(4.0), _sv(4.0), _sv(4.0))
    assert strategy_d(s) == s
    # but DOES fire on GAP
    g = (_sv(4.0), _sv(4.0), _sv(1.0))
    out = strategy_d(g)
    assert out[-1].support_state == 2.0


def test_strategy_e_bumps_anchor_density() -> None:
    s = (_sv(1.0), _sv(1.0, anchor=0.1))
    out = strategy_e(s)
    assert out[-1].anchor_density == 0.5  # 0.1 * 5


def test_strategy_e_does_not_change_support() -> None:
    s = (_sv(1.0), _sv(1.0, anchor=0.1))
    out = strategy_e(s)
    assert out[-1].support_state == s[-1].support_state


def test_strategy_g_combines_d_and_e() -> None:
    g = (_sv(4.0), _sv(4.0, anchor=0.1), _sv(1.0, anchor=0.2))
    out = strategy_g(g)
    assert out[-1].support_state == 2.0       # from D
    assert out[-1].anchor_density == 1.0      # 0.2 * 5


def test_apply_strategy_dispatch() -> None:
    s = (_sv(4.0), _sv(1.0))
    assert apply_strategy(
        s, StrategyKind.A_NO_CHANGE.value,
    ) == s
    assert apply_strategy(
        s, "unknown_strategy",
    ) == s  # safe fallback


def test_resolve_all_strategies_on_gaps_count() -> None:
    """7 strategies × 2 GAPs = 14 outcomes."""
    assert len(
        resolve_all_strategies_on_gaps()
    ) == 14


def test_resolve_on_corpus_covers_corpus() -> None:
    outs = resolve_on_corpus(
        StrategyKind.A_NO_CHANGE.value,
    )
    assert len(outs) == len(
        list(extract_all_trajectories()),
    )


def test_strategy_a_resolves_zero() -> None:
    r = build_report()
    sr = next(
        s for s in r.strategy_results
        if s.strategy == "A_no_change"
    )
    assert sr.resolved_count == 0
    assert sr.overcontrol_count == 0


def test_strategy_d_resolves_both_zero_overcontrol() -> None:
    """D fires only on GAP cases so it cannot
    overcontrol SUPPORTED trajectories."""
    r = build_report()
    sr = next(
        s for s in r.strategy_results
        if s.strategy == "D_bridge_expansion"
    )
    assert sr.resolved_count == 2
    assert sr.overcontrol_count == 0
    assert sr.nc_resolution_fp == 0.0


def test_strategy_g_resolves_both_zero_overcontrol() -> None:
    r = build_report()
    sr = next(
        s for s in r.strategy_results
        if s.strategy == "G_bridge_and_premise"
    )
    assert sr.resolved_count == 2
    assert sr.overcontrol_count == 0


def test_strategy_b_resolves_one() -> None:
    """Strategy B (apply_k_holds) audit-withdrawal
    succeeds for darwin (states[-2].support = 4.0) but
    not for mozart (states[-2].support = 1.0)."""
    r = build_report()
    sr = next(
        s for s in r.strategy_results
        if s.strategy == "B_confidence_hold"
    )
    assert sr.resolved_count == 1


def test_strategy_c_resolves_both() -> None:
    """audit_delay uses states[-3] which for both
    cases is SUPPORTED (4.0)."""
    r = build_report()
    sr = next(
        s for s in r.strategy_results
        if s.strategy == "C_audit_delay"
    )
    assert sr.resolved_count == 2


def test_strategy_e_resolves_zero() -> None:
    """Premise re-extraction does not touch
    support_state, so no GAP is resolved."""
    r = build_report()
    sr = next(
        s for s in r.strategy_results
        if s.strategy == "E_premise_re_extraction"
    )
    assert sr.resolved_count == 0


def test_terminal_failure_class_is_false() -> None:
    """At least one strategy resolves at least one
    GAP → not a robust terminal failure class."""
    assert build_report().terminal_failure_class is False


def test_best_strategy_resolved_count_meets_concept_gate() -> None:
    """Concept Gate #4: resolved_count > 0 OR
    terminal failure class. In this corpus
    resolved_count == 2 satisfies the OR cleanly."""
    r = build_report()
    assert r.resolved_count > 0 or r.terminal_failure_class


def test_best_strategy_is_d_or_g() -> None:
    r = build_report()
    assert r.best_strategy in {
        StrategyKind.D_BRIDGE_EXPANSION.value,
        StrategyKind.G_BRIDGE_AND_PREMISE.value,
    }


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "GAP_FULLY_RESOLVED",
        "GAP_PARTIALLY_RESOLVED",
        "GAP_TERMINAL_FAILURE_CLASS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_fully_resolved() -> None:
    assert build_report().recommendation == (
        "GAP_FULLY_RESOLVED"
    )


def test_gap_resolution_artifact_count() -> None:
    art = build_gap_resolution_artifact()
    assert art["outcome_count"] == 14


def test_terminal_gap_claims_artifact_count() -> None:
    art = build_terminal_gap_claims_artifact()
    assert art["claim_count"] == 2
    # Both have at least D and G in their resolved_by
    for c in art["claims"]:
        assert "D_bridge_expansion" in c["resolved_by_strategies"]
        assert "G_bridge_and_premise" in c["resolved_by_strategies"]


def test_concept_gate_summary() -> None:
    """All four directive Concept Gate conditions
    evaluated end-to-end."""
    from desi.gap_detected.report import (
        build_report as v346,
    )
    from desi.gap_detected_geometry.report import (
        build_report as v347,
    )
    r46 = v346()
    r47 = v347()
    r48 = build_report()
    # Gate 1
    assert r46.terminal_gap_count >= 2
    # Gate 2 - replay stability across all sprints
    assert r46.gap_replay_stability == 1.0
    assert r47.replay_stability == 1.0
    assert r48.replay_stability == 1.0
    # Gate 3
    assert r47.gap_cluster_count >= 1
    # Gate 4
    assert r48.resolved_count > 0 or r48.terminal_failure_class


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_48" / "report.json").read_text(
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
