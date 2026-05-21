"""v32.4 - Evolution Benchmark Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.frozen_benchmark_verdict import (
    BENCHMARK_CLASSES, GATE_PASS_STATEMENT, BenchmarkClass,
    aggregate, artifact_identity, blind_validation, build_go_no_go,
    build_report, build_verdict_artifact, class_meaning, class_rank,
    classify_corpus, evolution_traceability, gate_conditions,
    gate_failing_conditions, gate_passes_all, governance_identity,
    human_approval_enforcement, is_acceptable,
    measured_evolutionary_improvement, replay_stability,
)
from desi.frozen_benchmark_verdict.report import (
    REPORT_VERDICTS, VERDICT_VALIDATED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "frozen_benchmark"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert BENCHMARK_CLASSES == tuple(
        c.value for c in BenchmarkClass
    )
    assert len(BENCHMARK_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in BENCHMARK_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        BenchmarkClass.A_REAL_VALIDATED_IMPROVEMENT.value
    ) > class_rank(
        BenchmarkClass.E_EPISTEMICALLY_DEGRADED.value
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(
        BenchmarkClass.A_REAL_VALIDATED_IMPROVEMENT.value
    )
    assert is_acceptable(
        BenchmarkClass.C_NEUTRAL_COMPLEXITY_INCREASE.value
    )
    assert not is_acceptable(
        BenchmarkClass.D_OVERENGINEERED_DRIFT.value
    )
    assert not is_acceptable(
        BenchmarkClass.E_EPISTEMICALLY_DEGRADED.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["measured_evolutionary_improvement"].value >= 0.20
    assert by["governance_identity"].value == 1.0
    assert by["artifact_identity"].value == 1.0
    assert by["human_approval_enforcement"].value == 1.0
    assert by["evolution_traceability"].value >= 0.95
    assert by["replay_stability"].value == 1.0


def test_measured_improvement_real() -> None:
    assert measured_evolutionary_improvement() >= 0.20


def test_identity_metrics_full() -> None:
    assert governance_identity() == 1.0
    assert artifact_identity() == 1.0
    assert evolution_traceability() >= 0.95


def test_human_approval_enforcement_full() -> None:
    assert human_approval_enforcement() == 1.0


def test_blind_validation_full() -> None:
    assert blind_validation() == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "messbare" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.measured_evolutionary_improvement, m.governance_identity,
        m.artifact_identity, m.human_approval_enforcement,
        m.evolution_traceability, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


# --- classification -----------------------------
def test_corpus_class_real_validated() -> None:
    assert classify_corpus() == (
        BenchmarkClass.A_REAL_VALIDATED_IMPROVEMENT.value
    )


def test_corpus_not_drift_or_degraded() -> None:
    bad = {
        BenchmarkClass.D_OVERENGINEERED_DRIFT.value,
        BenchmarkClass.E_EPISTEMICALLY_DEGRADED.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in BENCHMARK_CLASSES:
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
    assert build_report().recommendation == VERDICT_VALIDATED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_report_records_local_attractors() -> None:
    # honest reporting of the v32.3 finding
    assert "neo4j_evolution_graph" in build_report().local_attractors


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v32_4_verdict.json")
    assert art["schema_version"] == (
        "v32_4_evolution_benchmark_verdict"
    )


def test_artifact_versions() -> None:
    art = _load("v32_4_verdict.json")
    assert art["baseline_version"] == "DESi_baseline_frozen_v1"
    assert art["mutated_version"] == "DESi_mutated_v31"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v32_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "real and measured" in disc
    assert "not projected" in disc
    assert "byte-identical" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v32_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "measured_evolutionary_improvement", "governance_identity",
        "artifact_identity", "human_approval_enforcement",
        "evolution_traceability", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v32_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == "EVOLUTION_IMPROVEMENT_VALIDATED"
    assert art["classification"] == (
        "real_validated_evolutionary_improvement"
    )
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v32_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_frozen_benchmark_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_rules() -> None:
    doc = _read("desi_frozen_benchmark_go_no_go.md")
    assert "blind_evaluation = TRUE" in doc
    assert "HUMAN_APPROVAL_REQUIRED" in doc
    assert "synthetic benchmark inflation" in doc


def test_go_no_go_lists_baseline() -> None:
    doc = _read("desi_frozen_benchmark_go_no_go.md")
    assert "DESi_baseline_frozen_v1" in doc
    assert "DESi_mutated_v31" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_frozen_benchmark_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_frozen_benchmark_go_no_go.md")
    assert doc == build_go_no_go()
