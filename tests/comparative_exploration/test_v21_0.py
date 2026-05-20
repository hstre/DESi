"""v21.0 - Comparative Exploration Governance tests."""
from __future__ import annotations

import json
import pathlib

from desi.comparative_exploration import (
    THESIS, build_comparison_artifact, build_report,
    comparison_table, delta_authority_drift,
    delta_exploration_diversity, delta_hallucination_pressure,
    delta_novelty_gain, delta_replay_stability, desi_alone,
    dual_agent, gate_conditions, gate_failing_conditions,
    gate_passes_all, paper_readiness_score, productivity_gain,
    readiness_checklist,
)
from desi.comparative_exploration.report import (
    REPORT_VERDICTS, VERDICT_DUAL_BETTER,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "dual_agent"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def _doc() -> str:
    return (
        _ARTIFACT_ROOT
        / "desi_comparative_exploration_go_no_go.md"
    ).read_text(encoding="utf-8")


# --- the dual-agent advantage -------------------
def test_dual_agent_adds_novelty() -> None:
    assert delta_novelty_gain() > 0.0


def test_dual_agent_adds_diversity() -> None:
    assert delta_exploration_diversity() > 0.0


def test_more_productive_than_desi_alone() -> None:
    assert productivity_gain() > 0.0
    assert (
        dual_agent()["exploration_diversity"]
        > desi_alone()["exploration_diversity"]
    )


# --- safety is not broken -----------------------
def test_hallucination_stays_safe() -> None:
    """The residual (uncontained) hallucination delta stays
    below the safety ceiling."""
    assert delta_hallucination_pressure() <= 0.10


def test_authority_drift_safe() -> None:
    assert delta_authority_drift() <= 0.05


def test_replay_preserved() -> None:
    assert delta_replay_stability() == 0.0
    assert desi_alone()["replay_stability"] == 1.0
    assert dual_agent()["replay_stability"] == 1.0


# --- gate / paper readiness ---------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_paper_ready() -> None:
    assert paper_readiness_score() >= 0.80
    # every checklist item met
    assert all(readiness_checklist().values())


def test_comparison_table_shape() -> None:
    table = comparison_table()
    for dim in (
        "redundancy_reduction", "novelty_gain",
        "exploration_diversity", "hallucination_pressure",
        "authority_drift", "capture_resistance",
        "replay_stability",
    ):
        assert dim in table
        row = table[dim]
        assert set(row) == {"desi_alone", "dual_agent", "delta"}


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_dual_better() -> None:
    assert build_report().recommendation == VERDICT_DUAL_BETTER


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_thesis_established() -> None:
    r = build_report()
    assert r.thesis == THESIS
    assert "without breaking epistemic safety" in r.thesis


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v21_0_comparison.json")
    assert art["schema_version"] == (
        "v21_0_comparative_exploration_governance"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v21_0_comparison.json")
    disc = art["disclaimer"].lower()
    assert "no rl is replaced" in disc
    assert "not an agi" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v21_0_comparison.json")
    required = {
        "delta_novelty_gain",
        "delta_exploration_diversity",
        "delta_redundancy_reduction",
        "delta_hallucination_pressure",
        "delta_authority_drift",
        "delta_replay_stability",
        "paper_readiness_score",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v21_0_comparison.json")
    live = build_comparison_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert "DUAL_AGENT_ADDS_EPISTEMIC_VALUE" in doc
    assert (
        "Controlled wild exploration improves ICRL-governed "
        "exploration without breaking epistemic safety" in doc
    )
