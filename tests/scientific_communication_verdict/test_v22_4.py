"""v22.4 - Scientific Communication Verdict tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.scientific_rendering import FORBIDDEN_TERMS, forbidden_hits
from desi.scientific_communication_verdict import (
    SCIENTIFIC_COMM_CLASSES, ScientificCommClass, aggregate,
    build_report, build_verdict_artifact, claim_conservatism,
    classify_corpus, epistemic_humility, gate_conditions,
    gate_failing_conditions, gate_passes_all, hype_resistance,
    paper_compatibility, technical_grounding,
)
from desi.scientific_communication_verdict.classification import (
    GATE_PASS_STATEMENT,
)
from desi.scientific_communication_verdict.report import (
    PHASE_VERDICTS, VERDICT_GROUNDED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "scientific_rendering"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def _doc() -> str:
    return (
        _ARTIFACT_ROOT / "desi_scientific_rendering_go_no_go.md"
    ).read_text(encoding="utf-8")


def _paper() -> str:
    return (
        _ARTIFACT_ROOT / "draft_exploration_governance_paper.md"
    ).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert SCIENTIFIC_COMM_CLASSES == tuple(
        c.value for c in ScientificCommClass
    )
    assert len(SCIENTIFIC_COMM_CLASSES) == 5


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["hype_resistance"].value >= 0.90
    assert by["claim_conservatism"].value >= 0.90
    assert by["technical_grounding"].value >= 0.90
    assert by["epistemic_humility"].value >= 0.90
    assert by["paper_compatibility"].value >= 0.90
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne epistemische Inflation oder AGI-Hype" in (
        r.gate_statement
    )


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.hype_resistance, m.claim_conservatism,
        m.technical_grounding, m.epistemic_humility,
        m.paper_compatibility, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_quality_high() -> None:
    assert hype_resistance() >= 0.90
    assert claim_conservatism() >= 0.90
    assert technical_grounding() >= 0.90
    assert epistemic_humility() >= 0.90
    assert paper_compatibility() >= 0.90


# --- classification -----------------------------
def test_corpus_class_exploratory_but_stable() -> None:
    assert classify_corpus() == (
        ScientificCommClass.C_EXPLORATORY_BUT_STABLE.value
    )


def test_corpus_not_hype_or_inflated() -> None:
    bad = {
        ScientificCommClass.D_HYPE_DRIFTED.value,
        ScientificCommClass.E_EPISTEMICALLY_INFLATED.value,
    }
    assert classify_corpus() not in bad


# --- the hard governance rule -------------------
def test_draft_paper_has_no_forbidden_terms() -> None:
    """The final document must contain none of the forbidden
    terms - that would be a governance failure."""
    paper = _paper()
    assert forbidden_hits(paper) == ()
    # also a direct word-boundary scan as a backstop
    low = paper.lower()
    for term in FORBIDDEN_TERMS:
        t = term.lower()
        if " " in t or "-" in t:
            assert t not in low
        else:
            assert not re.search(rf"\b{re.escape(t)}\b", low)


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().metrics.replay_stability == 1.0


def test_recommendation_is_grounded() -> None:
    assert build_report().recommendation == VERDICT_GROUNDED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v22_4_verdict.json")
    assert art["schema_version"] == (
        "v22_4_scientific_communication_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v22_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "no global intelligence claim" in disc
    assert "no truth authority" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v22_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "hype_resistance", "claim_conservatism",
        "technical_grounding", "epistemic_humility",
        "paper_compatibility", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v22_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "SCIENTIFIC_COMMUNICATION_GROUNDED"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v22_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert "SCIENTIFIC_COMMUNICATION_GROUNDED" in doc
    assert "Concept Gate" in doc


def test_go_no_go_refuses_manifesto() -> None:
    doc = _doc()
    assert "Kein AGI-Manifest" in doc
    assert "Keine Superintelligenz" in doc
