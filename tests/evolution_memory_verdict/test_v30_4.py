"""v30.4 - Evolution Memory Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.evolution_memory_verdict import (
    EVOLUTION_CLASSES, GATE_PASS_STATEMENT, EvolutionClass,
    aggregate, build_go_no_go, build_report,
    build_verdict_artifact, class_meaning, class_rank,
    classify_corpus, gate_conditions, gate_failing_conditions,
    gate_passes_all, human_approval_enforcement, is_acceptable,
)
from desi.evolution_memory_verdict.report import (
    REPORT_VERDICTS, VERDICT_GOVERNED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "evolution_memory"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert EVOLUTION_CLASSES == tuple(
        c.value for c in EvolutionClass
    )
    assert len(EVOLUTION_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in EVOLUTION_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value
    ) > class_rank(
        EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(
        EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value
    )
    assert is_acceptable(
        EvolutionClass.C_PRODUCTIVE_DRIFTING.value
    )
    assert not is_acceptable(
        EvolutionClass.D_OPTIMIZATION_TRAPPED.value
    )
    assert not is_acceptable(
        EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["replay_integrity"].value >= 0.95
    assert by["governance_preservation"].value >= 0.95
    assert by["lineage_integrity"].value >= 0.95
    assert by["risk_visibility"].value >= 0.95
    assert by["human_approval_enforcement"].value == 1.0
    assert by["evolution_traceability"].value >= 0.95


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "epistemisch strukturieren" in r.gate_statement


# --- human approval -----------------------------
def test_human_approval_enforcement_full() -> None:
    assert human_approval_enforcement() == 1.0


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.replay_integrity, m.governance_preservation,
        m.lineage_integrity, m.risk_visibility,
        m.human_approval_enforcement, m.evolution_traceability,
    ):
        assert 0.0 <= v <= 1.0


# --- classification -----------------------------
def test_corpus_class_replay_governed() -> None:
    assert classify_corpus() == (
        EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value
    )


def test_corpus_not_trapped_or_unstable() -> None:
    bad = {
        EvolutionClass.D_OPTIMIZATION_TRAPPED.value,
        EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in EVOLUTION_CLASSES:
        assert class_meaning(c).strip()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_governed() -> None:
    assert build_report().recommendation == VERDICT_GOVERNED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v30_4_verdict.json")
    assert art["schema_version"] == (
        "v30_4_evolution_memory_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v30_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "read-only epistemic history" in disc
    assert "never deleted" in disc
    assert "implicit learning layer" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v30_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "replay_integrity", "governance_preservation",
        "lineage_integrity", "risk_visibility",
        "human_approval_enforcement", "evolution_traceability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v30_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "EVOLUTION_MEMORY_REPLAY_GOVERNED"
    )
    assert art["classification"] == (
        "replay_governed_evolutionary_memory"
    )
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v30_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_evolution_memory_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_safety_rule() -> None:
    doc = _read("desi_evolution_memory_go_no_go.md")
    assert "HUMAN_APPROVAL_REQUIRED" in doc
    assert "hidden learning" in doc
    assert "read-only" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_evolution_memory_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_evolution_memory_go_no_go.md")
    assert doc == build_go_no_go()
