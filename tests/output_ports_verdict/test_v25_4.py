"""v25.4 - Output Port Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.output_ports_verdict import (
    GATE_PASS_STATEMENT, PORT_CLASSES, PortClass, aggregate,
    build_go_no_go, build_report, build_verdict_artifact,
    citation_integrity, class_meaning, class_rank,
    classify_corpus, cross_port_consistency, gate_conditions,
    gate_failing_conditions, gate_passes_all, is_acceptable,
    no_naked_claims, port_schema_integrity, result_traceability,
)
from desi.output_ports_verdict.report import (
    REPORT_VERDICTS, VERDICT_PUBLISHABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "output_ports"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert PORT_CLASSES == tuple(c.value for c in PortClass)
    assert len(PORT_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in PORT_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(PortClass.A_PUBLICATION_READY.value) > (
        class_rank(PortClass.E_UNSAFE_RENDERER.value)
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(PortClass.A_PUBLICATION_READY.value)
    assert is_acceptable(
        PortClass.C_FORMAT_STABLE_INCOMPLETE.value
    )
    assert not is_acceptable(PortClass.D_CITATION_FRAGILE.value)
    assert not is_acceptable(PortClass.E_UNSAFE_RENDERER.value)


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["port_schema_integrity"].value >= 0.95
    assert by["citation_integrity"].value >= 0.95
    assert by["result_traceability"].value >= 0.95
    assert by["cross_port_consistency"].value >= 0.95
    assert by["no_naked_claims"].value >= 0.95
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "graph-gebundene" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.port_schema_integrity, m.citation_integrity,
        m.result_traceability, m.cross_port_consistency,
        m.no_naked_claims, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_no_naked_claims_full() -> None:
    assert no_naked_claims() >= 0.95


# --- classification -----------------------------
def test_corpus_class_publication_ready() -> None:
    assert classify_corpus() == (
        PortClass.A_PUBLICATION_READY.value
    )


def test_corpus_not_fragile_or_unsafe() -> None:
    bad = {
        PortClass.D_CITATION_FRAGILE.value,
        PortClass.E_UNSAFE_RENDERER.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in PORT_CLASSES:
        assert class_meaning(c).strip()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_publishable() -> None:
    assert build_report().recommendation == VERDICT_PUBLISHABLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v25_4_verdict.json")
    assert art["schema_version"] == "v25_4_output_port_verdict"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v25_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "does not write papers" in disc
    assert "replay-stable output ports" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v25_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "port_schema_integrity", "citation_integrity",
        "result_traceability", "cross_port_consistency",
        "no_naked_claims", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v25_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "OUTPUT_PORTS_PUBLICATION_READY"
    )
    assert art["classification"] == (
        "publication_ready_port_system"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v25_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_output_ports_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_no_naked_claims_rule() -> None:
    doc = _read("desi_output_ports_go_no_go.md")
    assert "Keine nackten Aussagen" in doc
    assert "Phantomzitate" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(_read("desi_output_ports_go_no_go.md")) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_output_ports_go_no_go.md")
    assert doc == build_go_no_go()
