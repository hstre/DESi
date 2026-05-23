"""v27.4 - Research Harvester Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.research_harvester_verdict import (
    GATE_PASS_STATEMENT, HARVESTER_CLASSES, HarvesterClass,
    aggregate, build_go_no_go, build_report,
    build_verdict_artifact, class_meaning, class_rank,
    classify_corpus, gate_conditions, gate_failing_conditions,
    gate_passes_all, is_acceptable,
)
from desi.research_harvester_verdict.report import (
    REPORT_VERDICTS, VERDICT_CONNECTED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "research_harvester"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert HARVESTER_CLASSES == tuple(
        c.value for c in HarvesterClass
    )
    assert len(HARVESTER_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in HARVESTER_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        HarvesterClass.A_EPISTEMICALLY_CONNECTED.value
    ) > class_rank(
        HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(
        HarvesterClass.A_EPISTEMICALLY_CONNECTED.value
    )
    assert is_acceptable(
        HarvesterClass.C_CONVERGENT_INCOMPLETE.value
    )
    assert not is_acceptable(
        HarvesterClass.D_HYPE_FRAGILE.value
    )
    assert not is_acceptable(
        HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["claim_extraction_consistency"].value >= 0.90
    assert by["lineage_visibility"].value >= 0.90
    assert by["conflict_preservation"].value >= 0.90
    assert by["epistemic_neutrality"].value >= 0.95
    assert by["graph_integrity"].value >= 0.95
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "epistemischen Claim-Raum" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.claim_extraction_consistency, m.lineage_visibility,
        m.open_question_visibility, m.conflict_preservation,
        m.epistemic_neutrality, m.graph_integrity,
        m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


# --- classification -----------------------------
def test_corpus_class_connected() -> None:
    assert classify_corpus() == (
        HarvesterClass.A_EPISTEMICALLY_CONNECTED.value
    )


def test_corpus_not_fragile_or_collapsed() -> None:
    bad = {
        HarvesterClass.D_HYPE_FRAGILE.value,
        HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in HARVESTER_CLASSES:
        assert class_meaning(c).strip()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_connected() -> None:
    assert build_report().recommendation == VERDICT_CONNECTED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v27_4_verdict.json")
    assert art["schema_version"] == (
        "v27_4_research_harvester_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v27_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "dynamic epistemic claim space" in disc
    assert "does not rank" in disc
    assert "read-only" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v27_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "lineage_visibility", "open_question_visibility",
        "conflict_preservation", "epistemic_neutrality",
        "graph_integrity", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v27_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "RESEARCH_CLAIM_SPACE_CONNECTED"
    )
    assert art["classification"] == "epistemically_connected"


def test_artifact_full_matches_live_build() -> None:
    art = _load("v27_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_research_harvester_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_safety_rule() -> None:
    doc = _read("desi_research_harvester_go_no_go.md")
    assert "bewertet keine Forschung" in doc
    assert "read-only" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_research_harvester_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_research_harvester_go_no_go.md")
    assert doc == build_go_no_go()
