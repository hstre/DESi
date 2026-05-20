"""v17.4 - Sensitive Document Integrity Verdict tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.sensitive_documents_verdict import (
    SENSITIVE_DOCUMENT_CLASSES, SensitiveDocumentClass,
    aggregate, association_resistance, build_report,
    build_verdict_artifact, classify_corpus,
    epistemic_integrity, false_certainty_rate,
    gate_conditions, gate_failing_conditions,
    gate_passes_all, provenance_visibility,
)
from desi.sensitive_documents_verdict.classification import (
    GATE_PASS_STATEMENT,
)
from desi.sensitive_documents_verdict.report import (
    PHASE_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "sensitive_documents"
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
        / "desi_sensitive_documents_go_no_go.md"
    ).read_text(encoding="utf-8")


# --- closed taxonomy / no-guilt safety ----------
def test_classes_closed_set() -> None:
    assert SENSITIVE_DOCUMENT_CLASSES == tuple(
        c.value for c in SensitiveDocumentClass
    )
    assert len(SENSITIVE_DOCUMENT_CLASSES) == 5


def test_no_guilt_or_authority_value() -> None:
    forbidden = {
        "guilty", "perpetrator", "suspect", "involved",
        "culprit", "blacklist",
    }
    tokens = set()
    for v in (
        list(SENSITIVE_DOCUMENT_CLASSES)
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
    assert by["false_certainty_rate"].value <= 0.05
    assert by["association_resistance"].value >= 0.90
    assert by["provenance_visibility"].value >= 0.90
    assert by["epistemic_integrity"].value >= 0.90
    assert by["dissent_preservation"].value >= 0.90
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne epistemische oder moralische" in (
        r.gate_statement
    )


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.epistemic_integrity, m.association_resistance,
        m.false_certainty_rate, m.provenance_visibility,
        m.dissent_preservation, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_resistance_and_integrity_high() -> None:
    assert association_resistance() >= 0.90
    assert epistemic_integrity() >= 0.90
    assert provenance_visibility() >= 0.90
    assert false_certainty_rate() <= 0.05


# --- classification -----------------------------
def test_corpus_class_is_contamination_heavy_stable() -> None:
    assert classify_corpus() == (
        SensitiveDocumentClass
        .C_CONTAMINATION_HEAVY_BUT_STABLE.value
    )


def test_corpus_not_hazardous_or_inflated() -> None:
    bad = {
        SensitiveDocumentClass.D_NARRATIVE_INFLATED.value,
        SensitiveDocumentClass
        .E_EPISTEMICALLY_HAZARDOUS.value,
    }
    assert classify_corpus() not in bad


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().metrics.replay_stability == 1.0


def test_recommendation_is_structured() -> None:
    assert build_report().recommendation == (
        VERDICT_STRUCTURED
    )


def test_recommendation_claims_no_authority() -> None:
    rec = build_report().recommendation.lower()
    assert "no_authority" in rec
    for w in ("guilty", "suspect", "reveal"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v17_4_verdict.json")
    assert art["schema_version"] == (
        "v17_4_sensitive_document_integrity_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v17_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "claims no epistemic or moral authority" in disc
    assert "identifies no one" in disc
    assert "mention != involvement" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v17_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "epistemic_integrity",
        "association_resistance",
        "false_certainty_rate",
        "provenance_visibility",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v17_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "SENSITIVE_SPACE_STRUCTURED_NO_AUTHORITY"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v17_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert "Erwähnung ≠ Beteiligung" in doc
    assert (
        "SENSITIVE_SPACE_STRUCTURED_NO_AUTHORITY" in doc
    )
    assert "Concept Gate" in doc


def test_go_no_go_states_gate_pass() -> None:
    doc = _doc()
    assert (
        "DESi kann sensible historische Dokumenträume "
        "strukturieren" in doc
    )


def test_go_no_go_refuses_authority_and_doxxing() -> None:
    doc = _doc()
    assert "Keine Tätermaschine" in doc
    assert "synthetisch" in doc
    assert "Opfer" in doc  # the absolute rules section
