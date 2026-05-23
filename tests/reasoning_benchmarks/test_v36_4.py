"""v36.4 - Reasoning Benchmark Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.reasoning_benchmarks_verdict import (
    GATE_PASS_STATEMENT, REASONING_CLASSES, ReasoningClass,
    aggregate, build_go_no_go, build_report, build_verdict_artifact,
    class_meaning, class_rank, classify_corpus, gate_conditions,
    gate_failing_conditions, gate_passes_all, governance_identity,
    instruction_score, is_acceptable, logic_score, multihop_score,
    replay_stability, scientific_grounding_score,
)
from desi.reasoning_benchmarks_verdict.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "reasoning_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert REASONING_CLASSES == tuple(c.value for c in ReasoningClass)
    assert len(REASONING_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in REASONING_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        ReasoningClass.A_REASONING_ROBUST.value
    ) > class_rank(ReasoningClass.E_EPISTEMICALLY_UNSAFE.value)


def test_acceptable_classes() -> None:
    assert is_acceptable(ReasoningClass.A_REASONING_ROBUST.value)
    assert is_acceptable(
        ReasoningClass.B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE.value
    )
    assert not is_acceptable(
        ReasoningClass.D_BENCHMARK_FRAGILE.value
    )
    assert not is_acceptable(
        ReasoningClass.E_EPISTEMICALLY_UNSAFE.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["instruction_score"].value >= 0.85
    assert by["scientific_grounding_score"].value >= 0.85
    assert by["logic_score"].value >= 0.80
    assert by["multihop_score"].value >= 0.80
    assert by["governance_identity"].value == 1.0
    assert by["replay_stability"].value == 1.0


def test_family_scores() -> None:
    assert instruction_score() >= 0.85
    assert scientific_grounding_score() >= 0.85
    assert logic_score() >= 0.80
    assert multihop_score() >= 0.80


def test_governance_and_replay() -> None:
    assert governance_identity() == 1.0
    assert replay_stability() == 1.0


def test_gate_statement_present() -> None:
    assert build_report().gate_statement == GATE_PASS_STATEMENT


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    for v in aggregate().to_dict().values():
        assert 0.0 <= v <= 1.0


# --- classification -----------------------------
def test_corpus_class_robust() -> None:
    assert classify_corpus() == (
        ReasoningClass.A_REASONING_ROBUST.value
    )


def test_corpus_not_fragile_or_unsafe() -> None:
    bad = {
        ReasoningClass.D_BENCHMARK_FRAGILE.value,
        ReasoningClass.E_EPISTEMICALLY_UNSAFE.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in REASONING_CLASSES:
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
    art = _load("v36_4_verdict.json")
    assert art["schema_version"] == (
        "v36_4_reasoning_benchmark_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v36_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "not llm task accuracy" in disc
    assert "not official leaderboard results" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v36_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "instruction_score", "scientific_grounding_score",
        "logic_score", "multihop_score", "governance_identity",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v36_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == "REASONING_BENCHMARKS_PASSED"
    assert art["classification"] == "reasoning_benchmark_robust"
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v36_4_verdict.json")
    assert art == build_verdict_artifact()


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_reasoning_benchmarks_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_honesty() -> None:
    doc = _read("desi_reasoning_benchmarks_go_no_go.md")
    assert "netzwerkfrei" in doc
    assert "KEINE" in doc
    assert "HUMAN_APPROVAL_REQUIRED" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_reasoning_benchmarks_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_reasoning_benchmarks_go_no_go.md")
    assert doc == build_go_no_go()
