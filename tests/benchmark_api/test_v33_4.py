"""v33.4 - Benchmark Compatibility Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.benchmark_api_verdict import (
    COMPATIBILITY_CLASSES, GATE_PASS_STATEMENT, CompatibilityClass,
    aggregate, benchmark_mapping_integrity, build_go_no_go,
    build_report, build_verdict_artifact, class_meaning, class_rank,
    classify_corpus, core_identity, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    governance_independence, is_acceptable, overfitting_resistance,
    replay_stability, scorecard_traceability,
)
from desi.benchmark_api_verdict.report import (
    REPORT_VERDICTS, VERDICT_COMPATIBLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "benchmark_api"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert COMPATIBILITY_CLASSES == tuple(
        c.value for c in CompatibilityClass
    )
    assert len(COMPATIBILITY_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in COMPATIBILITY_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value
    ) > class_rank(CompatibilityClass.E_BENCHMARK_UNSAFE.value)


def test_acceptable_classes() -> None:
    assert is_acceptable(
        CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value
    )
    assert is_acceptable(CompatibilityClass.B_ADAPTER_STABLE.value)
    assert not is_acceptable(
        CompatibilityClass.D_BENCHMARK_OVERFITTED.value
    )
    assert not is_acceptable(
        CompatibilityClass.E_BENCHMARK_UNSAFE.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["core_identity"].value == 1.0
    assert by["governance_independence"].value >= 0.95
    assert by["benchmark_mapping_integrity"].value >= 0.95
    assert by["scorecard_traceability"].value >= 0.95
    assert by["overfitting_resistance"].value >= 0.95
    assert by["replay_stability"].value == 1.0


def test_core_unchanged() -> None:
    assert core_identity() == 1.0


def test_governance_independent() -> None:
    assert governance_independence() >= 0.95


def test_overfitting_resisted() -> None:
    assert overfitting_resistance() >= 0.95


def test_mapping_and_scorecards() -> None:
    assert benchmark_mapping_integrity() >= 0.95
    assert scorecard_traceability() >= 0.95


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "Governance" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    for v in aggregate().to_dict().values():
        assert 0.0 <= v <= 1.0


# --- classification -----------------------------
def test_corpus_class_compatible_governance() -> None:
    assert classify_corpus() == (
        CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value
    )


def test_corpus_not_overfitted_or_unsafe() -> None:
    bad = {
        CompatibilityClass.D_BENCHMARK_OVERFITTED.value,
        CompatibilityClass.E_BENCHMARK_UNSAFE.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in COMPATIBILITY_CLASSES:
        assert class_meaning(c).strip()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0
    assert build_report().replay_stability == 1.0


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_validated() -> None:
    assert build_report().recommendation == VERDICT_COMPATIBLE


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v33_4_verdict.json")
    assert art["schema_version"] == "v33_4_benchmark_api_verdict"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v33_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "test desi but never steer it" in disc
    assert "epistemic core is" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v33_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "core_identity", "governance_independence",
        "benchmark_mapping_integrity", "scorecard_traceability",
        "overfitting_resistance", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v33_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "BENCHMARK_COMPATIBILITY_VALIDATED"
    )
    assert art["classification"] == (
        "benchmark_compatible_governance_system"
    )
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v33_4_verdict.json")
    assert art == build_verdict_artifact()


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_benchmark_api_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_principle() -> None:
    doc = _read("desi_benchmark_api_go_no_go.md")
    assert "Benchmarks duerfen DESi testen" in doc
    assert "NICHT steuern" in doc
    assert "HUMAN_APPROVAL_REQUIRED" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_benchmark_api_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_benchmark_api_go_no_go.md")
    assert doc == build_go_no_go()
