"""v33.0 - Benchmark API Schema tests."""
from __future__ import annotations

import json
import pathlib

from desi.benchmark_api import (
    ALLOWED_BENCHMARK_OPERATIONS, FORBIDDEN_BENCHMARK_OPERATIONS,
    REQUIRED_BENCHMARKS, RESULT_FIELDS, SUPPORTED_BENCHMARKS,
    adversarial_task, bind_result, build_report,
    build_schema_artifact, canonical_task, canonical_tasks,
    core_identity, covers_core_boundary, governance_independence,
    is_forbidden, make_task, operation_boundary_visibility,
    output_traceability, refuse_result, replay_stability,
    requested_forbidden, schema_complete, schema_coverage,
)
from desi.benchmark_api.report import (
    REPORT_VERDICTS, VERDICT_DEFINED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_api"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- coverage / boundary ------------------------
def test_six_required_families_supported() -> None:
    assert set(REQUIRED_BENCHMARKS).issubset(set(SUPPORTED_BENCHMARKS))
    assert schema_coverage() == 1.0


def test_operation_boundary_visibility_full() -> None:
    assert operation_boundary_visibility() == 1.0


def test_canonical_tasks_are_valid() -> None:
    tasks = canonical_tasks()
    assert len(tasks) == 6
    for t in tasks:
        assert t.is_valid()
        assert t.boundary_explicit()
        assert covers_core_boundary(t.forbidden_operations)


# --- output / traceability ----------------------
def test_output_traceability_full() -> None:
    assert output_traceability() == 1.0


def test_result_fields_replay_bound() -> None:
    for f in ("replay_hash", "provenance", "governance_status"):
        assert f in RESULT_FIELDS


def test_bound_result_is_traceable() -> None:
    task = canonical_task("DRIFT_BENCHMARK")
    res = bind_result(
        task,
        claim_outputs=(("c1", "v1"),),
        metrics=(("claim_drift", 0.0),),
        provenance=("test",),
        limitations=("synthetic",),
    )
    assert res.is_traceable()
    assert schema_complete(res)
    assert res.is_replay_bound()


# --- governance independence / core -------------
def test_governance_independence_full() -> None:
    assert governance_independence() == 1.0


def test_core_identity_full() -> None:
    assert core_identity() == 1.0


# --- benchmarks cannot steer --------------------
def test_adversarial_task_rejected() -> None:
    adv = adversarial_task()
    assert adv.is_valid() is False
    assert requested_forbidden(adv) != ()


def test_forbidden_covers_protected_core() -> None:
    for area in (
        "replay_kernel", "determinism_scanner", "concept_gates",
        "governance_core", "authority_filters",
    ):
        assert is_forbidden(f"modify_{area}")


def test_corruption_vectors_forbidden() -> None:
    for op in (
        "score_hacking", "hidden_test_adaptation",
        "benchmark_overfitting", "replay_bypass",
        "concept_gate_modification",
    ):
        assert is_forbidden(op)


def test_forbidden_and_allowed_disjoint() -> None:
    assert not (
        set(ALLOWED_BENCHMARK_OPERATIONS)
        & set(FORBIDDEN_BENCHMARK_OPERATIONS)
    )


def test_refusal_keeps_governance_independent() -> None:
    task = make_task(
        task_id="t",
        benchmark_name="DRIFT_BENCHMARK",
        payload={"claims": 1},
        allowed_operations=("adapter",),
    )
    res = refuse_result(task, "test refusal")
    assert res.is_refusal()
    assert res.governance_status == "GOVERNANCE_INDEPENDENT"


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        schema_coverage(), operation_boundary_visibility(),
        output_traceability(), governance_independence(),
        replay_stability(), core_identity(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_defined() -> None:
    assert build_report().recommendation == VERDICT_DEFINED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v33_0_schema.json")
    assert art["schema_version"] == "v33_0_benchmark_api_schema"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v33_0_schema.json")
    disc = art["disclaimer"].lower()
    assert "test desi but never steer it" in disc
    assert "governance is read from the core" in disc


def test_artifact_lists_six_canonical_tasks() -> None:
    art = _load("v33_0_schema.json")
    assert len(art["canonical_tasks"]) == 6


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v33_0_schema.json")
    required = {
        "schema_coverage", "operation_boundary_visibility",
        "output_traceability", "governance_independence",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v33_0_schema.json")
    assert art == build_schema_artifact()
