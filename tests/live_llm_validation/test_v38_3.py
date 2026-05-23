"""v38.3 - Routing & Governance Benchmark tests (real captures)."""
from __future__ import annotations

import json
import pathlib

from desi.live_llm_validation_routing import (
    ROUTE_DEEPSEEK, ROUTE_GRANITE, build_report,
    build_routing_artifact, deepseek_escalation_rate,
    governance_stability, quality_preservation, replay_stability,
    routed_tasks, routing_cost_reduction, routing_metrics,
    should_escalate, unnecessary_escalations,
)
from desi.live_llm_validation_routing.cost_optimizer import (
    routed_down_efficiency, total_workload_cost_reduction,
)
from desi.live_llm_validation_routing.report import (
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


# --- routing decisions --------------------------
def test_eleven_real_routed_tasks() -> None:
    tasks = routed_tasks()
    assert len(tasks) == 11


def test_structured_routed_to_granite() -> None:
    for t in routed_tasks():
        if t.complexity == "low":
            assert t.routed_model == ROUTE_GRANITE


def test_semantic_escalated_to_deepseek() -> None:
    for t in routed_tasks():
        if t.complexity == "high":
            assert t.routed_model == ROUTE_DEEPSEEK
            assert should_escalate(t)


def test_no_unnecessary_escalations() -> None:
    assert unnecessary_escalations() == 0


# --- cost (honest, three views) -----------------
def test_routing_cost_reduction_meets_floor() -> None:
    assert routing_cost_reduction() >= 0.50


def test_routed_down_efficiency_high() -> None:
    # cheap-routed tasks save almost all of the DeepSeek cost
    assert routed_down_efficiency() > 0.90


def test_total_workload_reduction_reported() -> None:
    # honestly small because hard tasks dominate spend
    assert 0.0 <= total_workload_cost_reduction() <= 1.0


# --- quality / governance / replay --------------
def test_quality_preservation_full() -> None:
    assert quality_preservation() >= 0.85


def test_governance_and_replay() -> None:
    assert governance_stability() == 1.0
    assert replay_stability() == 1.0


def test_escalation_rate_reported() -> None:
    assert 0.0 <= deepseek_escalation_rate() <= 1.0


def test_metrics_in_unit_interval() -> None:
    for v in routing_metrics().values():
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
    art = _load("v38_3_routing.json")
    assert art["schema_version"] == "v38_3_routing_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v38_3_routing.json")
    disc = art["disclaimer"].lower()
    assert "real captured" in disc
    assert "never governance" in disc
    assert "no benchmark-specific routing hacks" in disc


def test_artifact_reports_all_cost_views() -> None:
    art = _load("v38_3_routing.json")
    assert "routing_cost_reduction" in art
    assert "total_workload_cost_reduction" in art
    assert "routed_down_efficiency" in art


def test_artifact_no_api_key_leak() -> None:
    art = _load("v38_3_routing.json")
    assert "sk-or-v1" not in json.dumps(art)


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v38_3_routing.json")
    required = {
        "routing_cost_reduction", "deepseek_escalation_rate",
        "quality_preservation", "governance_stability",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v38_3_routing.json")
    assert art == build_routing_artifact()
