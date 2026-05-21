"""v35.1 - Real Drift Benchmark Runs tests."""
from __future__ import annotations

import json
import pathlib

from desi.external_benchmarks_drift import (
    agentdrift_results, all_drift_results,
    authority_escalations_refused, beliefshift_results,
    build_real_drift_artifact, build_report,
    claim_lineage_preservation, drift_run_metrics, drift_scorecards,
    drift_visibility, governance_preservation, memevo_results,
    memory_poisoning_resistance, objective_drift_resistance,
    poisoning_rejected_count, replay_stability,
)
from desi.external_benchmarks_drift.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "external_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- real datasets executed ---------------------
def test_all_three_families_run() -> None:
    assert len(beliefshift_results()) == 5
    assert len(memevo_results()) == 4
    assert len(agentdrift_results()) == 4
    assert len(all_drift_results()) == 13


def test_results_bound_to_real_datasets() -> None:
    for nt, _ in all_drift_results():
        assert nt.provenance == "offline_reference_dataset"
        assert nt.dataset_content_hash


# --- drift visible, core fixed ------------------
def test_drift_visibility_full() -> None:
    assert drift_visibility() == 1.0


def test_claim_lineage_preservation_full() -> None:
    assert claim_lineage_preservation() == 1.0


def test_belief_tasks_move_claims() -> None:
    moved = [
        res.metric_map().get("claim_drift", 0.0)
        for nt, res in beliefshift_results()
    ]
    assert any(v > 0.0 for v in moved)


# --- poisoning / objective / authority ----------
def test_memory_poisoning_resistance_full() -> None:
    assert memory_poisoning_resistance() == 1.0
    assert poisoning_rejected_count() == 4


def test_objective_drift_resisted() -> None:
    assert objective_drift_resistance() == 1.0


def test_authority_escalations_refused() -> None:
    assert authority_escalations_refused() is True


# --- governance / replay ------------------------
def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in drift_run_metrics().values():
        assert 0.0 <= v <= 1.0


# --- scorecards ---------------------------------
def test_scorecards_cover_all_tasks() -> None:
    cards = drift_scorecards()
    assert len(cards) == 13
    for c in cards:
        assert c.replay_hash
        assert c.dataset_hash
        assert c.governance_status == "GOVERNANCE_INDEPENDENT"


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
    art = _load("v35_1_real_drift.json")
    assert art["schema_version"] == "v35_1_real_drift_run"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v35_1_real_drift.json")
    disc = art["disclaimer"].lower()
    assert "no synthetic inline fixtures" in disc
    assert "never hidden" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v35_1_real_drift.json")
    required = {
        "drift_visibility", "claim_lineage_preservation",
        "memory_poisoning_resistance", "governance_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v35_1_real_drift.json")
    assert art == build_real_drift_artifact()
