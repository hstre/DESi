"""v5.5 — recommendation gate and report artifact."""
from __future__ import annotations

import hashlib
import json
import pathlib

from ._helpers import load_claims


_ARTIFACT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "v5_5" / "report.json"
)


def _load_report() -> dict:
    return json.loads(_ARTIFACT.read_text(encoding="utf-8"))


def test_report_recommendation_is_v5_line_frozen() -> None:
    assert _load_report()["recommendation"] == (
        "V5_LINE_FROZEN"
    )


def test_report_recommendation_in_closed_set() -> None:
    allowed = {
        "V5_LINE_FROZEN", "V5_LINE_INCOMPLETE", "NONE",
    }
    assert _load_report()["recommendation"] in allowed


def test_report_claim_count_matches_claims_json() -> None:
    rep = _load_report()
    assert rep["claim_count"] == len(load_claims())


def test_report_paper_metrics_meet_thresholds() -> None:
    rep = _load_report()
    assert rep["claim_count"] >= 140
    assert rep["failed_hypotheses"] >= 12
    assert rep["drift_findings"] == 0
    assert rep["contradiction_count"] == 0
    assert rep["missing_pin_count"] == 0


def test_report_lists_required_findings() -> None:
    rep = _load_report()
    expected = {
        "METHODOLOGY_TRANSFER_CONFIRMED",
        "TAXONOMY_STABLE",
        "TAXONOMY_GENERALIZES",
        "CORPUS_FIT_TO_TAXONOMY",
        "TAXONOMY_GENERALIZES_PROBES_FAIL",
    }
    found = set(rep["required_findings"])
    missing = expected - found
    assert not missing, missing


def test_report_artifact_section_count_is_fifteen() -> None:
    assert _load_report()["section_count"] == 15
