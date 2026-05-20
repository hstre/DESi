"""v18.4 - Metaphysical Governance Verdict tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.metaphysical_governance_verdict import (
    METAPHYSICAL_GOVERNANCE_CLASSES,
    MetaphysicalGovernanceClass, aggregate,
    authority_resistance, build_report,
    build_verdict_artifact, capture_resistance,
    classify_corpus, dissent_preservation,
    epistemic_plurality, false_certainty_rate,
    gate_conditions, gate_failing_conditions,
    gate_passes_all,
)
from desi.metaphysical_governance_verdict.classification import (
    GATE_PASS_STATEMENT,
)
from desi.metaphysical_governance_verdict.report import (
    PHASE_VERDICTS, VERDICT_SURVIVED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "religious_pressure"
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
        / "desi_metaphysical_governance_go_no_go.md"
    ).read_text(encoding="utf-8")


# --- closed taxonomy / no-authority safety ------
def test_classes_closed_set() -> None:
    assert METAPHYSICAL_GOVERNANCE_CLASSES == tuple(
        c.value for c in MetaphysicalGovernanceClass
    )
    assert len(METAPHYSICAL_GOVERNANCE_CLASSES) == 5


def test_no_truth_or_ranking_vocab() -> None:
    forbidden = {
        "true", "truest", "superior", "proven",
        "divine", "best",
    }
    tokens = set()
    for v in (
        list(METAPHYSICAL_GOVERNANCE_CLASSES)
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
    assert by["epistemic_plurality"].value >= 0.90
    assert by["authority_resistance"].value >= 0.90
    assert by["capture_resistance"].value >= 0.90
    assert by["dissent_preservation"].value >= 0.90
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne selbst dogmatisch" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.epistemic_plurality, m.authority_resistance,
        m.capture_resistance, m.dissent_preservation,
        m.false_certainty_rate, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_resistance_and_plurality_high() -> None:
    assert epistemic_plurality() >= 0.90
    assert authority_resistance() >= 0.90
    assert capture_resistance() >= 0.90
    assert dissent_preservation() >= 0.90
    assert false_certainty_rate() <= 0.05


# --- classification -----------------------------
def test_corpus_class_is_conflict_rich_stable() -> None:
    assert classify_corpus() == (
        MetaphysicalGovernanceClass
        .C_CONFLICT_RICH_BUT_STABLE.value
    )


def test_corpus_not_compressed_or_captured() -> None:
    bad = {
        MetaphysicalGovernanceClass
        .D_DOGMATICALLY_COMPRESSED.value,
        MetaphysicalGovernanceClass
        .E_IDEOLOGICALLY_CAPTURED.value,
    }
    assert classify_corpus() not in bad


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().metrics.replay_stability == 1.0


def test_recommendation_is_survived() -> None:
    assert build_report().recommendation == VERDICT_SURVIVED


def test_recommendation_claims_no_authority() -> None:
    rec = build_report().recommendation.lower()
    assert "no_authority" in rec
    for w in ("true_religion", "superior", "proven"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v18_4_verdict.json")
    assert art["schema_version"] == (
        "v18_4_metaphysical_governance_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v18_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "determines no true religion" in disc
    assert "ranks no tradition" in disc
    assert (
        "theological meaning != empirical verifiability"
        in disc
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v18_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "epistemic_plurality",
        "authority_resistance",
        "capture_resistance",
        "dissent_preservation",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v18_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "METAPHYSICAL_PRESSURE_SURVIVED_NO_AUTHORITY"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v18_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert (
        "METAPHYSICAL_PRESSURE_SURVIVED_NO_AUTHORITY" in doc
    )
    assert "Concept Gate" in doc
    assert "Theologische Bedeutung ≠ empirische" in doc


def test_go_no_go_states_gate_pass() -> None:
    doc = _doc()
    assert (
        "DESi kann metaphysischen Wahrheitsdruck "
        "analysieren" in doc
    )


def test_go_no_go_refuses_authority() -> None:
    doc = _doc()
    assert "Keine Religionsmaschine" in doc
    assert "rankt keine Tradition" in doc
    assert "synthetisch" in doc
