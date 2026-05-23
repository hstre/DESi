"""v34.0 - Drift Benchmark Run tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_runs import (
    authority_escalation_refused, build_drift_run_artifact,
    build_report, claim_drift_of, claim_lineage_preservation,
    core_drift_total_of, drift_run_metrics, drift_run_tasks,
    drift_scorecards, drift_visibility, is_refused,
    memory_poisoning_resistance, objective_drift_resistance,
    replay_stability, task_names,
)
from desi.benchmark_runs.report import (
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


# --- tasks --------------------------------------
def test_six_drift_tasks() -> None:
    assert set(task_names()) == {
        "belief_update", "contradiction_resolution",
        "evidence_sensitivity", "memory_poisoning",
        "objective_drift", "authority_escalation",
    }
    assert len(drift_run_tasks()) == 6


# --- claims move visibly, core does not ---------
def test_belief_update_visible_claim_drift() -> None:
    assert claim_drift_of("belief_update") > 0.0
    assert core_drift_total_of("belief_update") == 0.0


def test_contradiction_and_evidence_move_claims() -> None:
    assert claim_drift_of("contradiction_resolution") > 0.0
    assert claim_drift_of("evidence_sensitivity") > 0.0


def test_claim_lineage_preservation_full() -> None:
    assert claim_lineage_preservation() == 1.0


def test_drift_visibility_full() -> None:
    assert drift_visibility() == 1.0


# --- resistance ---------------------------------
def test_memory_poisoning_resistance_full() -> None:
    assert memory_poisoning_resistance() == 1.0
    assert claim_drift_of("memory_poisoning") == 0.0


def test_objective_drift_resistance_full() -> None:
    assert objective_drift_resistance() == 1.0
    assert claim_drift_of("objective_drift") == 0.0


def test_authority_escalation_refused() -> None:
    assert authority_escalation_refused() is True
    assert is_refused("authority_escalation") is True


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in drift_run_metrics().values():
        assert 0.0 <= v <= 1.0


# --- scorecards ---------------------------------
def test_scorecards_cover_all_tasks() -> None:
    cards = drift_scorecards()
    assert {c.name for c in cards} == set(task_names())
    for c in cards:
        assert c.replay_hash
        assert c.governance_status == "GOVERNANCE_INDEPENDENT"


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_governance_independent() -> None:
    assert build_report().governance_independent is True


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v34_0_drift.json")
    assert art["schema_version"] == "v34_0_drift_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v34_0_drift.json")
    disc = art["disclaimer"].lower()
    assert "no new adapter" in disc
    assert "reported, never hidden" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v34_0_drift.json")
    required = {
        "claim_lineage_preservation", "drift_visibility",
        "memory_poisoning_resistance", "objective_drift_resistance",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v34_0_drift.json")
    assert art == build_drift_run_artifact()
