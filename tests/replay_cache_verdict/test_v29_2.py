"""v29.2 - Comparative Real Benchmark Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.replay_cache_verdict import (
    CLASS_VALIDATED, GATE_PASS_STATEMENT, RESULT_CLASSES,
    artifact_identity, build_report, build_verdict_artifact,
    classify_result, gate_conditions, gate_failing_conditions,
    gate_passes_all, governance_identity,
    measured_runtime_improvement, recompute_counts,
    regression_survival, replay_stability,
)
from desi.replay_cache_verdict.report import (
    REPORT_VERDICTS, VERDICT_REAL,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "replay_cache_evolution"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- concept gate (5 conditions) ----------------
def test_gate_has_five_conditions() -> None:
    assert len(gate_conditions()) == 5


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["measured_runtime_improvement"].value >= 0.20
    assert by["artifact_identity"].value == 1.0
    assert by["governance_identity"].value == 1.0
    assert by["regression_survival"].value == 1.0
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "branch-isoliert" in r.gate_statement


# --- real measured improvement ------------------
def test_measured_runtime_improvement_above_floor() -> None:
    assert measured_runtime_improvement() >= 0.20


def test_recompute_counts_reduced() -> None:
    base, cached = recompute_counts()
    assert cached < base


# --- safety identities --------------------------
def test_artifact_identity_full() -> None:
    assert artifact_identity() == 1.0


def test_governance_identity_full() -> None:
    assert governance_identity() == 1.0


def test_regression_survival_full() -> None:
    assert regression_survival() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        measured_runtime_improvement(), artifact_identity(),
        governance_identity(), regression_survival(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- classification -----------------------------
def test_classify_validated() -> None:
    assert classify_result() == CLASS_VALIDATED
    assert classify_result() in set(RESULT_CLASSES)


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_real() -> None:
    assert build_report().recommendation == VERDICT_REAL


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_human_approval_required() -> None:
    assert build_report().human_approval_required is True


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v29_2_verdict.json")
    assert art["schema_version"] == "v29_2_replay_cache_verdict"


def test_artifact_is_branch_isolated() -> None:
    art = _load("v29_2_verdict.json")
    assert art["branch"] == "proposal/replay_cache_v1"
    assert art["branch"] != "main"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v29_2_verdict.json")
    disc = art["disclaimer"].lower()
    assert "measured" in disc
    assert "not projected" in disc
    assert "nothing is merged" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v29_2_verdict.json")
    required = {
        "measured_runtime_improvement", "artifact_identity",
        "governance_identity", "regression_survival",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v29_2_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "REAL_INFRA_EVOLUTION_VALIDATED"
    )
    assert art["classification"] == "real_validated_improvement"
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v29_2_verdict.json")
    live = build_verdict_artifact()
    assert art == live
