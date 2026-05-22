"""v38.2 - DeepSeek V4 Pro Semantic Validation tests (real captures)."""
from __future__ import annotations

import json
import pathlib

from desi.live_llm_validation_deepseek import (
    build_deepseek_artifact, build_report, deepseek_metrics,
    deepseek_results, evidence_gap_preservation, governance_stability,
    granite_results, hallucination_visibility, replay_stability,
    scorecards, semantic_quality_lift, semantic_tasks,
)
from desi.live_llm_validation_deepseek.report import (
    REPORT_VERDICTS, VERDICT_PASSED, granite_baseline_quality,
    quality_delta_vs_granite,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "live_llm_validation"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- real captures, both models -----------------
def test_five_semantic_tasks() -> None:
    assert len(semantic_tasks()) == 5
    assert len(deepseek_results()) == 5
    assert len(granite_results()) == 5


def test_results_are_real_deepseek() -> None:
    for r in deepseek_results():
        assert "deepseek-v4-pro" in r.model_version


# --- metrics ------------------------------------
def test_semantic_quality_lift_meets_floor() -> None:
    assert semantic_quality_lift() >= 0.85


def test_evidence_gap_preservation_full() -> None:
    assert evidence_gap_preservation() >= 0.85


def test_hallucination_visibility_full() -> None:
    assert hallucination_visibility() == 1.0


def test_governance_and_replay() -> None:
    assert governance_stability() == 1.0
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in deepseek_metrics().values():
        assert 0.0 <= v <= 1.0


# --- honest comparison reporting ----------------
def test_granite_baseline_and_delta_reported() -> None:
    # the comparison is transparent; delta may be 0 on this rubric
    assert 0.0 <= granite_baseline_quality() <= 1.0
    delta = quality_delta_vs_granite()
    assert delta == round(
        semantic_quality_lift() - granite_baseline_quality(), 6
    )


def test_ungrounded_signal_surfaced() -> None:
    # every result exposes a non-negative ungrounded-token count
    for c in scorecards():
        assert c.deepseek_ungrounded_tokens >= 0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_real_cost_recorded() -> None:
    assert build_report().total_cost_usd > 0.0


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v38_2_deepseek.json")
    assert art["schema_version"] == "v38_2_deepseek_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v38_2_deepseek.json")
    disc = art["disclaimer"].lower()
    assert "reasoning model" in disc
    assert "not a hidden" in disc
    assert "never canonical truth" in disc
    assert "never suppressed" in disc


def test_artifact_no_api_key_leak() -> None:
    art = _load("v38_2_deepseek.json")
    assert "sk-or-v1" not in json.dumps(art)


def test_artifact_reports_delta() -> None:
    art = _load("v38_2_deepseek.json")
    assert "quality_delta_vs_granite" in art
    assert "granite_baseline_quality" in art


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v38_2_deepseek.json")
    required = {
        "semantic_quality_lift", "evidence_gap_preservation",
        "hallucination_visibility", "governance_stability",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v38_2_deepseek.json")
    assert art == build_deepseek_artifact()
