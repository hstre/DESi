"""v19.4 - Exploration Governance Verdict tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.icrl_governance_verdict import (
    EXPLORATION_GOVERNANCE_CLASSES,
    ExplorationGovernanceClass, aggregate,
    build_report, build_verdict_artifact, capture_resistance,
    classify_corpus, exploration_preservation,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    hidden_authority_drift, novelty_visibility,
    redundancy_reduction,
)
from desi.icrl_governance_verdict.classification import (
    GATE_PASS_STATEMENT,
)
from desi.icrl_governance_verdict.report import (
    PHASE_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "icrl_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def _doc() -> str:
    return (
        _ARTIFACT_ROOT / "desi_icrl_governance_go_no_go.md"
    ).read_text(encoding="utf-8")


# --- closed taxonomy / no hidden authority ------
def test_classes_closed_set() -> None:
    assert EXPLORATION_GOVERNANCE_CLASSES == tuple(
        c.value for c in ExplorationGovernanceClass
    )
    assert len(EXPLORATION_GOVERNANCE_CLASSES) == 5


def test_no_optimality_vocab() -> None:
    forbidden = {"optimal", "best", "global", "solved", "true"}
    tokens = set()
    for v in (
        list(EXPLORATION_GOVERNANCE_CLASSES)
        + list(PHASE_VERDICTS)
    ):
        tokens.update(re.split(r"[^a-z]+", v.lower()))
    assert not (tokens & forbidden)


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["redundancy_reduction"].value >= 0.40
    assert by["exploration_preservation"].value >= 0.90
    assert by["capture_resistance"].value >= 0.90
    assert by["novelty_visibility"].value >= 0.90
    assert by["hidden_authority_drift"].value <= 0.05
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne versteckte Optimierungsautoritaet" in (
        r.gate_statement
    )


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.redundancy_reduction, m.exploration_preservation,
        m.capture_resistance, m.novelty_visibility,
        m.hidden_authority_drift, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_governance_quality_high() -> None:
    assert redundancy_reduction() >= 0.40
    assert exploration_preservation() >= 0.90
    assert capture_resistance() >= 0.90
    assert novelty_visibility() >= 0.90
    assert hidden_authority_drift() <= 0.05


# --- classification -----------------------------
def test_corpus_class_is_conflict_rich_stable() -> None:
    assert classify_corpus() == (
        ExplorationGovernanceClass
        .C_CONFLICT_RICH_BUT_STABLE.value
    )


def test_corpus_not_collapsed_or_captured() -> None:
    bad = {
        ExplorationGovernanceClass
        .D_EXPLORATION_COLLAPSED.value,
        ExplorationGovernanceClass
        .E_TRAJECTORY_CAPTURED.value,
    }
    assert classify_corpus() not in bad


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().metrics.replay_stability == 1.0


def test_recommendation_is_structured() -> None:
    assert build_report().recommendation == VERDICT_STRUCTURED


def test_recommendation_claims_no_authority() -> None:
    rec = build_report().recommendation.lower()
    assert "no_hidden_authority" in rec
    for w in ("optimal", "solved", "best"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v19_4_verdict.json")
    assert art["schema_version"] == (
        "v19_4_exploration_governance_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v19_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "replaces no rl policy" in disc
    assert "manipulates no reward" in disc
    assert "no hidden optimisation authority" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v19_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "redundancy_reduction",
        "exploration_preservation",
        "capture_resistance",
        "novelty_visibility",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v19_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "EXPLORATION_STRUCTURED_NO_HIDDEN_AUTHORITY"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v19_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert (
        "EXPLORATION_STRUCTURED_NO_HIDDEN_AUTHORITY" in doc
    )
    assert "Concept Gate" in doc


def test_go_no_go_states_gate_pass() -> None:
    doc = _doc()
    assert (
        "DESi kann Exploration epistemisch strukturieren"
        in doc
    )


def test_go_no_go_refuses_optimisation_authority() -> None:
    doc = _doc()
    assert "Kein AGI-Paper" in doc
    assert "ersetzt RL" in doc
