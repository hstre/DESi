"""v34.3 - Scientific Rendering & Citation Benchmark Run tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_runs_rendering import (
    RENDERING_CHECKS, build_rendering_artifact, build_report,
    citation_completeness, limitation_visibility, live_phantoms,
    naked_claims, no_naked_claims, paper_port_compliance,
    paper_quality_scorecard, phantom_citation_resistance,
    rendering_metrics, replay_stability, result_traceability,
)
from desi.benchmark_runs_rendering.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_runs"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- checks defined -----------------------------
def test_six_rendering_checks() -> None:
    assert "phantom_citation_detection" in RENDERING_CHECKS
    assert "no_naked_claims" in RENDERING_CHECKS
    assert "paper_port_compliance" in RENDERING_CHECKS
    assert len(RENDERING_CHECKS) == 6


# --- phantom citations rejected -----------------
def test_phantom_citation_resistance_full() -> None:
    assert phantom_citation_resistance() == 1.0
    assert live_phantoms() == ()


# --- citation completeness / traceability -------
def test_citation_completeness_full() -> None:
    assert citation_completeness() == 1.0


def test_no_naked_claims() -> None:
    assert no_naked_claims() is True
    assert naked_claims() == ()


def test_result_traceability_full() -> None:
    assert result_traceability() == 1.0


# --- limitations / compliance -------------------
def test_limitation_visibility_full() -> None:
    assert limitation_visibility() == 1.0


def test_paper_port_compliance_full() -> None:
    assert paper_port_compliance() == 1.0


def test_scorecard_complete() -> None:
    c = paper_quality_scorecard()
    assert c.phantom_citation_resistance == 1.0
    assert c.citation_completeness == 1.0
    assert c.limitation_visibility == 1.0


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in rendering_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v34_3_scientific_rendering.json")
    assert art["schema_version"] == "v34_3_scientific_rendering_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v34_3_scientific_rendering.json")
    disc = art["disclaimer"].lower()
    assert "no citation fabrication" in disc
    assert "phantom citations are detected and rejected" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v34_3_scientific_rendering.json")
    required = {
        "phantom_citation_resistance", "citation_completeness",
        "result_traceability", "limitation_visibility",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v34_3_scientific_rendering.json")
    assert art == build_rendering_artifact()
