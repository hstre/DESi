"""v37.2 - Audit Reasoning & Evidence Benchmark tests."""
from __future__ import annotations

import json
import pathlib

from desi.audit_benchmarks_reasoning import (
    ASSERTION_TYPES, all_procedures, assertion_mapping_integrity,
    audit_tasks, build_reasoning_artifact, build_report, conclusion,
    evidence_gap_visibility, gap_tasks, is_material,
    materiality_traceability, missing_evidence, reasoning_metrics,
    replay_stability, unsupported_conclusion_resistance,
)
from desi.audit_benchmarks_reasoning.report import (
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


# --- evidence gaps surfaced ---------------------
def test_evidence_gap_visibility_full() -> None:
    assert evidence_gap_visibility() == 1.0


def test_gap_tasks_detected() -> None:
    gap_ids = {t.task_id for t in gap_tasks()}
    assert gap_ids == {"ar_002", "ar_003"}
    for t in gap_tasks():
        assert missing_evidence(t)


# --- no unsupported conclusions -----------------
def test_unsupported_conclusion_resistance_full() -> None:
    assert unsupported_conclusion_resistance() == 1.0


def test_gaps_yield_insufficient_evidence() -> None:
    for t in gap_tasks():
        assert conclusion(t) == "insufficient_evidence"


def test_complete_tasks_supported() -> None:
    by = {t.task_id: t for t in audit_tasks()}
    assert conclusion(by["ar_001"]) == "supported"
    assert conclusion(by["ar_004"]) == "supported"


def test_procedures_proposed_for_gaps() -> None:
    procs = all_procedures()
    assert "ar_002" in procs
    assert "ar_003" in procs


# --- assertion mapping / materiality ------------
def test_assertion_mapping_integrity_full() -> None:
    assert assertion_mapping_integrity() == 1.0
    for t in audit_tasks():
        assert t.assertion in ASSERTION_TYPES


def test_materiality_traceability_full() -> None:
    assert materiality_traceability() == 1.0


def test_materiality_decision() -> None:
    by = {t.task_id: t for t in audit_tasks()}
    assert is_material(by["ar_003"]) is True
    assert is_material(by["ar_005"]) is False


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in reasoning_metrics().values():
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
    art = _load("v37_2_reasoning.json")
    assert art["schema_version"] == "v37_2_audit_reasoning_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v37_2_reasoning.json")
    disc = art["disclaimer"].lower()
    assert "insufficient_evidence" in disc
    assert "never draws a supported conclusion without evidence" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v37_2_reasoning.json")
    required = {
        "evidence_gap_visibility", "unsupported_conclusion_resistance",
        "assertion_mapping_integrity", "materiality_traceability",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v37_2_reasoning.json")
    assert art == build_reasoning_artifact()
