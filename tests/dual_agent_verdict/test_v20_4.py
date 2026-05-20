"""v20.4 - Dual-Agent Governance Verdict tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.dual_agent_verdict import (
    DUAL_AGENT_CLASSES, DualAgentClass, aggregate,
    authority_resistance, build_report,
    build_verdict_artifact, classify_corpus,
    exploration_diversity, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    hallucination_containment, novelty_preservation,
    productive_conflict, productivity_gain, wild_not_eliminated,
)
from desi.dual_agent_verdict.classification import (
    GATE_PASS_STATEMENT,
)
from desi.dual_agent_verdict.report import (
    PHASE_VERDICTS, VERDICT_GOVERNED,
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
        _ARTIFACT_ROOT / "desi_dual_agent_go_no_go.md"
    ).read_text(encoding="utf-8")


# --- closed taxonomy / no optimality vocab ------
def test_classes_closed_set() -> None:
    assert DUAL_AGENT_CLASSES == tuple(
        c.value for c in DualAgentClass
    )
    assert len(DUAL_AGENT_CLASSES) == 5


def test_no_optimality_vocab() -> None:
    forbidden = {"optimal", "best", "global", "solved", "true"}
    tokens = set()
    for v in list(DUAL_AGENT_CLASSES) + list(PHASE_VERDICTS):
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
    assert by["hallucination_containment"].value >= 0.90
    assert by["novelty_preservation"].value >= 0.90
    assert by["authority_resistance"].value >= 0.90
    assert by["productive_conflict"].value >= 0.90
    assert by["exploration_diversity"].value >= 0.90
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne Exploration oder epistemische Freiheit" in (
        r.gate_statement
    )


# --- metrics + the productivity case ------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.hallucination_containment, m.novelty_preservation,
        m.authority_resistance, m.productive_conflict,
        m.exploration_diversity, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_governance_quality_high() -> None:
    assert hallucination_containment() >= 0.90
    assert novelty_preservation() >= 0.90
    assert authority_resistance() >= 0.90
    assert productive_conflict() >= 0.90
    assert exploration_diversity() >= 0.90


def test_wild_brother_is_productive() -> None:
    """The phase Killerfrage: the governed wild brother is
    more productive than conservative governance alone, and
    is not eliminated."""
    assert productivity_gain() > 0.0
    assert wild_not_eliminated() is True


# --- classification -----------------------------
def test_corpus_class_is_conflict_rich_productive() -> None:
    assert classify_corpus() == (
        DualAgentClass.C_CONFLICT_RICH_BUT_PRODUCTIVE.value
    )


def test_corpus_not_drifted_or_collapsed() -> None:
    bad = {
        DualAgentClass.D_HALLUCINATION_DRIFTED.value,
        DualAgentClass.E_AUTHORITY_COLLAPSED.value,
    }
    assert classify_corpus() not in bad


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().metrics.replay_stability == 1.0


def test_recommendation_is_governed() -> None:
    assert build_report().recommendation == VERDICT_GOVERNED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v20_4_verdict.json")
    assert art["schema_version"] == (
        "v20_4_dual_agent_governance_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v20_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "without replacing the" in disc
    assert "hidden optimisation authority" in disc
    assert "eliminating or homogenising" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v20_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "hallucination_containment",
        "novelty_preservation",
        "authority_resistance",
        "productive_conflict",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v20_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == "WILD_EXPLORATION_GOVERNED"


def test_artifact_full_matches_live_build() -> None:
    art = _load("v20_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert "WILD_EXPLORATION_GOVERNED" in doc
    assert "Concept Gate" in doc
    assert "productivity_gain" in doc


def test_go_no_go_refuses_agi() -> None:
    doc = _doc()
    assert "Kein AGI-Paper" in doc
    assert "ersetzt RL" in doc
