"""v36.1 - Scientific Fact Checking (SciFact / QASper) tests."""
from __future__ import annotations

import json
import pathlib

from desi.reasoning_benchmarks_scifact import (
    answer_grounding, build_report, build_scifact_artifact,
    citation_integrity, derive_label, evidence_alignment,
    is_unsupported, qasper_tasks, scifact_metrics, scifact_tasks,
    unanswerable_flagged, unsupported_claim_rejection,
)
from desi.reasoning_benchmarks_scifact.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "reasoning_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- evidence alignment -------------------------
def test_datasets_loaded() -> None:
    assert len(scifact_tasks()) == 5
    assert len(qasper_tasks()) == 4


def test_evidence_alignment_full() -> None:
    assert evidence_alignment() == 1.0


def test_labels_derived_from_evidence() -> None:
    labels = {t.claim_id: derive_label(t) for t in scifact_tasks()}
    assert labels["sf_001"] == "SUPPORTED"
    assert labels["sf_002"] == "REFUTED"
    assert labels["sf_003"] == "NOT_ENOUGH_INFO"


# --- evidence gaps not hidden -------------------
def test_unsupported_claim_rejection_full() -> None:
    assert unsupported_claim_rejection() == 1.0


def test_evidence_gaps_surface_as_nei() -> None:
    nei = [t for t in scifact_tasks() if t.label == "NOT_ENOUGH_INFO"]
    assert nei
    for t in nei:
        assert is_unsupported(t)


# --- citations / grounding ----------------------
def test_citation_integrity_full() -> None:
    assert citation_integrity() == 1.0


def test_answer_grounding_full() -> None:
    assert answer_grounding() == 1.0
    assert unanswerable_flagged() is True


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert scifact_metrics()["replay_stability"] == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in scifact_metrics().values():
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
    art = _load("v36_1_scifact_qasper.json")
    assert art["schema_version"] == "v36_1_scifact_qasper_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v36_1_scifact_qasper.json")
    disc = art["disclaimer"].lower()
    assert "not_enough_info" in disc
    assert "not official leaderboard results" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v36_1_scifact_qasper.json")
    required = {
        "evidence_alignment", "unsupported_claim_rejection",
        "citation_integrity", "answer_grounding", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v36_1_scifact_qasper.json")
    assert art == build_scifact_artifact()
