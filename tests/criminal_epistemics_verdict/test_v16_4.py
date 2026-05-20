"""v16.4 - Criminal Epistemics Verdict tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.criminal_epistemics_verdict import (
    CRIMINAL_EPISTEMICS_CLASSES,
    CriminalEpistemicsClass, aggregate,
    build_report, build_verdict_artifact,
    classify_corpus, epistemic_integrity,
    gate_conditions, gate_failing_conditions,
    gate_passes_all, speculation_resistance,
)
from desi.criminal_epistemics_verdict.classification import (
    GATE_PASS_STATEMENT,
)
from desi.criminal_epistemics_verdict.report import (
    PHASE_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "criminal_epistemics"
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
        / "desi_criminal_epistemics_go_no_go.md"
    ).read_text(encoding="utf-8")


# --- closed taxonomy / no forbidden vocab -------
def test_classes_closed_set() -> None:
    assert CRIMINAL_EPISTEMICS_CLASSES == tuple(
        c.value for c in CriminalEpistemicsClass
    )
    assert len(CRIMINAL_EPISTEMICS_CLASSES) == 5


def test_no_truth_or_guilt_value() -> None:
    forbidden = {
        "guilty", "solved", "perpetrator",
        "culprit", "conspiracy", "true",
    }
    tokens = set()
    for v in (
        list(CRIMINAL_EPISTEMICS_CLASSES)
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
    assert by["speculation_resistance"].value >= 0.90
    assert by["dissent_preservation"].value >= 0.90
    assert by["epistemic_integrity"].value >= 0.90
    assert by[
        "independent_evidence_preservation"
    ].value >= 0.90
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne narrative Autoritaet" in (
        r.gate_statement
    )


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.epistemic_integrity, m.speculation_resistance,
        m.false_certainty_rate, m.dissent_preservation,
        m.independent_evidence_preservation,
        m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_resistance_and_integrity_high() -> None:
    assert speculation_resistance() >= 0.90
    assert epistemic_integrity() >= 0.90


# --- classification -----------------------------
def test_corpus_class_is_conflict_heavy_stable() -> None:
    """The Kennedy corpus is genuinely contested but
    DESi holds it stable - class C."""
    assert classify_corpus() == (
        CriminalEpistemicsClass
        .C_CONFLICT_HEAVY_BUT_STABLE.value
    )


def test_corpus_not_destabilized() -> None:
    bad = {
        CriminalEpistemicsClass
        .D_SPECULATION_DOMINATED.value,
        CriminalEpistemicsClass
        .E_MYTHOLOGICALLY_UNSTABLE.value,
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
    assert "no_narrative_authority" in rec
    for w in ("solved", "guilty", "true"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v16_4_verdict.json")
    assert art["schema_version"] == (
        "v16_4_criminal_epistemics_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v16_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "claims no" in disc
    assert "names no" in disc
    assert "neither solved nor unsolved" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v16_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "epistemic_integrity",
        "speculation_resistance",
        "false_certainty_rate",
        "dissent_preservation",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v16_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "CASE_STRUCTURED_NO_NARRATIVE_AUTHORITY"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v16_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert "Wahrheitsmaschine" in doc
    assert (
        "CASE_STRUCTURED_NO_NARRATIVE_AUTHORITY"
        in doc
    )
    assert "Concept Gate" in doc


def test_go_no_go_states_gate_pass() -> None:
    doc = _doc()
    assert (
        "DESi kann historische Kriminalfälle "
        "epistemisch strukturieren" in doc
    )


def test_go_no_go_refuses_authority() -> None:
    doc = _doc()
    # explicit refusals
    assert "keine endgültigen Täter" in doc or (
        "keine" in doc and "Täter" in doc
    )
    assert "ist gelöst" in doc  # only in the NICHT list
    assert "SPECULATIVE" in doc
