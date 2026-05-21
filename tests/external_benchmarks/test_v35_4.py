"""v35.4 - Real External Benchmark Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.external_benchmarks_verdict import (
    GATE_PASS_STATEMENT, REAL_BENCHMARK_CLASSES, RealBenchmarkClass,
    aggregate, build_go_no_go, build_report, build_verdict_artifact,
    class_meaning, class_rank, classify_corpus, core_identity,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    governance_stability, is_acceptable, real_drift_score,
    real_search_score, replay_stability, reproducibility_score,
)
from desi.external_benchmarks_verdict.report import (
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


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert REAL_BENCHMARK_CLASSES == tuple(
        c.value for c in RealBenchmarkClass
    )
    assert len(REAL_BENCHMARK_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in REAL_BENCHMARK_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        RealBenchmarkClass.A_EXTERNALLY_ROBUST.value
    ) > class_rank(RealBenchmarkClass.E_BENCHMARK_UNSAFE.value)


def test_acceptable_classes() -> None:
    assert is_acceptable(
        RealBenchmarkClass.A_EXTERNALLY_ROBUST.value
    )
    assert is_acceptable(
        RealBenchmarkClass.B_EXTERNALLY_COMPATIBLE.value
    )
    assert not is_acceptable(
        RealBenchmarkClass.D_BENCHMARK_FRAGILE.value
    )
    assert not is_acceptable(
        RealBenchmarkClass.E_BENCHMARK_UNSAFE.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["real_drift_score"].value >= 0.85
    assert by["real_search_score"].value >= 0.85
    assert by["reproducibility_score"].value >= 0.95
    assert by["governance_stability"].value >= 0.95
    assert by["core_identity"].value == 1.0
    assert by["replay_stability"].value == 1.0


def test_family_scores() -> None:
    assert real_drift_score() >= 0.85
    assert real_search_score() >= 0.85
    assert reproducibility_score() >= 0.95


def test_core_governance_replay() -> None:
    assert core_identity() == 1.0
    assert governance_stability() >= 0.95
    assert replay_stability() == 1.0


def test_gate_statement_present() -> None:
    assert build_report().gate_statement == GATE_PASS_STATEMENT


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    for v in aggregate().to_dict().values():
        assert 0.0 <= v <= 1.0


# --- classification -----------------------------
def test_corpus_class_externally_robust() -> None:
    assert classify_corpus() == (
        RealBenchmarkClass.A_EXTERNALLY_ROBUST.value
    )


def test_corpus_not_fragile_or_unsafe() -> None:
    bad = {
        RealBenchmarkClass.D_BENCHMARK_FRAGILE.value,
        RealBenchmarkClass.E_BENCHMARK_UNSAFE.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in REAL_BENCHMARK_CLASSES:
        assert class_meaning(c).strip()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0
    assert build_report().replay_stability == 1.0


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v35_4_verdict.json")
    assert art["schema_version"] == (
        "v35_4_real_external_benchmark_verdict"
    )


def test_artifact_carries_honest_disclaimer() -> None:
    art = _load("v35_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "not official leaderboard results" in disc
    assert "network-free" in disc
    assert "no benchmark steering" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v35_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "real_drift_score", "real_search_score",
        "reproducibility_score", "governance_stability",
        "core_identity", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v35_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == "REAL_EXTERNAL_BENCHMARKS_PASSED"
    assert art["classification"] == (
        "externally_benchmark_robust_epistemic_system"
    )
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v35_4_verdict.json")
    assert art == build_verdict_artifact()


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_real_external_benchmarks_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_honesty() -> None:
    doc = _read("desi_real_external_benchmarks_go_no_go.md")
    assert "netzwerkfrei" in doc
    assert "KEINE" in doc
    assert "HUMAN_APPROVAL_REQUIRED" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_real_external_benchmarks_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_real_external_benchmarks_go_no_go.md")
    assert doc == build_go_no_go()
