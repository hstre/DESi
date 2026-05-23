"""v33.1 - Drift Benchmark Adapter tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_api_drift import (
    CORE_DRIFT_DIMENSIONS, DRIFT_FORMS, INTERNAL_DRIFT_DIMENSIONS,
    all_forms_keep_core_fixed, artifact_is_stable,
    belief_shift, belief_shift_is_visible, build_drift_artifact,
    build_report, claim_lineage_preservation,
    contradiction_claim_drift, drift_mapping_integrity,
    drift_metrics, drift_visibility, evidence_claim_drift,
    governance_preservation, map_form, memory_poisoning_rejected,
    objective_is_pinned, replay_stability,
)
from desi.benchmark_api_drift.report import (
    REPORT_VERDICTS, VERDICT_MAPPED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_api"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- mapping integrity --------------------------
def test_six_drift_forms() -> None:
    assert set(DRIFT_FORMS) == {
        "belief_drift", "output_drift", "objective_drift",
        "memory_poisoning", "contradiction_resolution",
        "evidence_sensitivity",
    }


def test_drift_mapping_integrity_full() -> None:
    assert drift_mapping_integrity() == 1.0


def test_every_form_maps_all_dimensions() -> None:
    for form in DRIFT_FORMS:
        assert set(map_form(form)) == set(INTERNAL_DRIFT_DIMENSIONS)


# --- core never drifts --------------------------
def test_core_dimensions_always_zero() -> None:
    for form in DRIFT_FORMS:
        mapped = map_form(form)
        for dim in CORE_DRIFT_DIMENSIONS:
            assert mapped[dim] == 0.0, (form, dim)


def test_all_forms_keep_core_fixed() -> None:
    assert all_forms_keep_core_fixed() is True


# --- claims may move, visibly -------------------
def test_belief_drift_is_visible_and_nonzero() -> None:
    assert belief_shift("belief_drift") > 0.0
    assert belief_shift_is_visible("belief_drift") is True


def test_contradiction_and_evidence_move_claims() -> None:
    assert contradiction_claim_drift() > 0.0
    assert evidence_claim_drift() > 0.0


def test_objective_drift_resisted() -> None:
    assert objective_is_pinned() is True
    assert map_form("objective_drift")["claim_drift"] == 0.0


def test_memory_poisoning_rejected() -> None:
    assert memory_poisoning_rejected() is True


def test_output_artifact_stable() -> None:
    assert artifact_is_stable() is True


# --- visibility / lineage -----------------------
def test_drift_visibility_full() -> None:
    assert drift_visibility() == 1.0


def test_claim_lineage_preservation_full() -> None:
    assert claim_lineage_preservation() == 1.0


# --- governance / replay ------------------------
def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in drift_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_mapped() -> None:
    assert build_report().recommendation == VERDICT_MAPPED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v33_1_drift_adapter.json")
    assert art["schema_version"] == "v33_1_drift_adapter"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v33_1_drift_adapter.json")
    disc = art["disclaimer"].lower()
    assert "reported, never hidden" in disc
    assert "never drifts" in disc


def test_artifact_form_mappings_complete() -> None:
    art = _load("v33_1_drift_adapter.json")
    assert set(art["form_mappings"]) == set(DRIFT_FORMS)


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v33_1_drift_adapter.json")
    required = {
        "drift_mapping_integrity", "claim_lineage_preservation",
        "drift_visibility", "governance_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v33_1_drift_adapter.json")
    assert art == build_drift_artifact()
