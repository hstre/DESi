"""v37.1 - Semantic Audit Risk Benchmark tests."""
from __future__ import annotations

import json
import pathlib

from desi.audit_benchmarks_risk import (
    all_flags, build_report, build_risk_artifact, detect_types,
    implicit_inconsistency_detection, narrative_tension_detection,
    replay_stability, risk_metrics, risk_scenarios,
    semantic_risk_visibility, uncertainty_preservation,
)
from desi.audit_benchmarks_risk.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "audit_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- risk visibility ----------------------------
def test_semantic_risk_visibility_full() -> None:
    assert semantic_risk_visibility() == 1.0


def test_all_expected_risks_detected() -> None:
    for s in risk_scenarios():
        detected = set(detect_types(s.get("signals", {})))
        assert set(s["expected_risks"]).issubset(detected)


def test_narrative_tension_detection_full() -> None:
    assert narrative_tension_detection() == 1.0


def test_implicit_inconsistency_detection_full() -> None:
    assert implicit_inconsistency_detection() == 1.0


# --- no hallucinated certainty ------------------
def test_uncertainty_preservation_full() -> None:
    assert uncertainty_preservation() == 1.0


def test_every_flag_requires_evidence() -> None:
    flags = all_flags()
    assert flags
    for f in flags:
        assert f.severity == "flag"
        assert f.requires_evidence is True


def test_no_fraud_assertion_type() -> None:
    # risk types are flags, not fraud verdicts
    for f in all_flags():
        assert "fraud" not in f.risk_type


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in risk_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_governance_identity() -> None:
    assert build_report().governance_identity == 1.0


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v37_1_semantic_risk.json")
    assert art["schema_version"] == "v37_1_semantic_risk_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v37_1_semantic_risk.json")
    disc = art["disclaimer"].lower()
    assert "never asserts fraud" in disc
    assert "no hallucination" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v37_1_semantic_risk.json")
    required = {
        "semantic_risk_visibility", "narrative_tension_detection",
        "implicit_inconsistency_detection", "uncertainty_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v37_1_semantic_risk.json")
    assert art == build_risk_artifact()
