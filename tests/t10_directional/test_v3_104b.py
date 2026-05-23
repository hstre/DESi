"""v3.104b - T10 directional gate tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_directional.gate import (
    GateInput, directional_gate, old_gate,
)
from desi.t10_directional.report import (
    build_report,
    build_t10_directional_gate_artifact,
)
from desi.t10_directional.simulate import (
    ScenarioKind,
    all_scenario_outcomes,
    false_block_rate,
    false_pass_rate,
)


def _passing_input() -> GateInput:
    return GateInput(
        candidate_auc=1.0,
        injected_purity=1.0,
        injected_auc=1.0,
        adverse_flip_count=0,
        beneficial_flip_count=2,
        adverse_auc_delta=0.0,
        beneficial_auc_delta=0.30,
        historical_auc_delta=0.30,
        replay_stability=1.0,
    )


def test_old_gate_blocks_beneficial_drift() -> None:
    """The original gate cannot tell beneficial
    from adverse - any historical_auc_delta >
    0.05 is a fail."""
    g = _passing_input()
    result = old_gate(g)
    assert not result.passed
    assert "historical_auc_delta" in (
        result.failing_conditions
    )


def test_directional_gate_passes_beneficial_drift() -> None:
    """The refined gate only counts adverse
    drift."""
    g = _passing_input()
    result = directional_gate(g)
    assert result.passed
    assert result.failing_conditions == ()


def test_both_gates_block_real_damage() -> None:
    """An adverse_flip_count > 0 fails BOTH
    gates."""
    g = GateInput(
        candidate_auc=1.0,
        injected_purity=1.0,
        injected_auc=1.0,
        adverse_flip_count=1,
        beneficial_flip_count=0,
        adverse_auc_delta=0.0,
        beneficial_auc_delta=0.0,
        historical_auc_delta=0.0,
        replay_stability=1.0,
    )
    assert not old_gate(g).passed
    assert not directional_gate(g).passed


def test_both_gates_block_adverse_auc_drift() -> None:
    g = GateInput(
        candidate_auc=1.0,
        injected_purity=1.0,
        injected_auc=1.0,
        adverse_flip_count=0,
        beneficial_flip_count=0,
        adverse_auc_delta=0.30,
        beneficial_auc_delta=0.0,
        historical_auc_delta=0.30,
        replay_stability=1.0,
    )
    assert not old_gate(g).passed
    assert not directional_gate(g).passed


def test_three_scenarios_enumerated() -> None:
    assert len(all_scenario_outcomes()) == 3


def test_actual_t10_old_gate_fails() -> None:
    outs = all_scenario_outcomes()
    actual = next(
        o for o in outs
        if o.scenario
        == ScenarioKind.ACTUAL_T10.value
    )
    assert not actual.old_gate["passed"]


def test_actual_t10_directional_gate_passes() -> None:
    outs = all_scenario_outcomes()
    actual = next(
        o for o in outs
        if o.scenario
        == ScenarioKind.ACTUAL_T10.value
    )
    assert actual.directional_gate["passed"]


def test_synthetic_adverse_both_block() -> None:
    outs = all_scenario_outcomes()
    adv = next(
        o for o in outs
        if o.scenario
        == ScenarioKind.SYNTHETIC_ADVERSE.value
    )
    assert not adv.old_gate["passed"]
    assert not adv.directional_gate["passed"]


def test_synthetic_beneficial_only_dir_passes() -> None:
    outs = all_scenario_outcomes()
    bo = next(
        o for o in outs
        if o.scenario
        == ScenarioKind
        .SYNTHETIC_BENEFICIAL_ONLY.value
    )
    assert not bo.old_gate["passed"]
    assert bo.directional_gate["passed"]


def test_false_block_rate_drops_to_zero() -> None:
    """Killerfrage: blockiert das neue Gate nur
    echten Schaden? Yes - false_block_rate
    drops from 0.67 to 0.0."""
    assert false_block_rate(False) > 0.0
    assert false_block_rate(True) == 0.0


def test_false_pass_rate_remains_zero() -> None:
    """Neither gate accepts real damage."""
    assert false_pass_rate(False) == 0.0
    assert false_pass_rate(True) == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_dominant() -> None:
    assert build_report().recommendation == (
        "DIRECTIONAL_GATE_DOMINANT"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DIRECTIONAL_GATE_DOMINANT",
        "DIRECTIONAL_GATE_IMPROVES",
        "DIRECTIONAL_GATE_INCONCLUSIVE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_all_scenarios() -> None:
    art = build_t10_directional_gate_artifact()
    assert len(art["scenarios"]) == 3


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_104b" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable
