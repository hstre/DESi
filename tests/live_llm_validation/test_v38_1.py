"""v38.1 - Granite Structured Task Validation tests (real captures)."""
from __future__ import annotations

import json
import pathlib

from desi.live_llm_validation_granite import (
    build_granite_artifact, build_report, cost_efficiency,
    granite_metrics, granite_success_rate, hallucination_rate,
    is_compliant, replay_stability, results, schema_compliance,
    structured_tasks, task_by_id, total_cost,
)
from desi.live_llm_validation_granite.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "live_llm_validation"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- real captures evaluated --------------------
def test_six_structured_tasks() -> None:
    assert len(structured_tasks()) == 6
    assert len(results()) == 6


def test_results_are_real_captures() -> None:
    for r in results():
        assert r.content  # non-empty captured content


# --- metrics ------------------------------------
def test_granite_success_rate_meets_floor() -> None:
    assert granite_success_rate() >= 0.80


def test_schema_compliance_meets_floor() -> None:
    assert schema_compliance() >= 0.80


def test_hallucination_rate_low() -> None:
    assert hallucination_rate() <= 0.10


def test_cost_efficiency_high() -> None:
    assert cost_efficiency() >= 0.80


def test_real_cost_is_small_but_recorded() -> None:
    assert total_cost() > 0.0
    assert total_cost() < 0.01


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in granite_metrics().values():
        assert 0.0 <= v <= 1.0


# --- deterministic grading ----------------------
def test_compliance_check_is_deterministic() -> None:
    for r in results():
        task = task_by_id(r.task_id)
        assert is_compliant(task, r.content) == r.compliant


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
    art = _load("v38_1_granite.json")
    assert art["schema_version"] == "v38_1_granite_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v38_1_granite.json")
    disc = art["disclaimer"].lower()
    assert "real captured" in disc
    assert "never treated as canonical truth" in disc
    assert "never silently suppressed" in disc


def test_artifact_no_api_key_leak() -> None:
    art = _load("v38_1_granite.json")
    assert "sk-or-v1" not in json.dumps(art)


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v38_1_granite.json")
    required = {
        "granite_success_rate", "schema_compliance",
        "hallucination_rate", "cost_efficiency", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v38_1_granite.json")
    assert art == build_granite_artifact()
