"""v38.4 - Live LLM Validation Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.live_llm_validation_verdict import (
    LIVE_CLASSES, GATE_PASS_STATEMENT, LiveClass, aggregate,
    build_go_no_go, build_report, build_verdict_artifact,
    class_meaning, class_rank, classify_corpus, deepseek_score,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    governance_identity, granite_score, hallucination_containment,
    is_acceptable, replay_stability, routing_score,
)
from desi.live_llm_validation_verdict.report import (
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


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert LIVE_CLASSES == tuple(c.value for c in LiveClass)
    assert len(LIVE_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in LIVE_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        LiveClass.A_LIVE_VALIDATED.value
    ) > class_rank(LiveClass.E_GOVERNANCE_UNSAFE.value)


def test_acceptable_classes() -> None:
    assert is_acceptable(LiveClass.A_LIVE_VALIDATED.value)
    assert is_acceptable(LiveClass.B_STABLE_ROUTING.value)
    assert not is_acceptable(LiveClass.D_LIVE_UNSTABLE.value)
    assert not is_acceptable(LiveClass.E_GOVERNANCE_UNSAFE.value)


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["granite_score"].value >= 0.80
    assert by["deepseek_score"].value >= 0.85
    assert by["routing_score"].value >= 0.85
    assert by["governance_identity"].value == 1.0
    assert by["hallucination_containment"].value >= 0.90
    assert by["replay_stability"].value == 1.0


def test_scores() -> None:
    assert granite_score() >= 0.80
    assert deepseek_score() >= 0.85
    assert routing_score() >= 0.85
    assert hallucination_containment() >= 0.90


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
def test_corpus_class_live_validated() -> None:
    assert classify_corpus() == LiveClass.A_LIVE_VALIDATED.value


def test_corpus_not_unstable_or_unsafe() -> None:
    bad = {
        LiveClass.D_LIVE_UNSTABLE.value,
        LiveClass.E_GOVERNANCE_UNSAFE.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in LIVE_CLASSES:
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
    art = _load("v38_4_verdict.json")
    assert art["schema_version"] == "v38_4_live_llm_validation_verdict"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v38_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "real captured" in disc
    assert "never canonical truth" in disc
    assert "no api key in the repo" in disc
    assert "never silently suppressed" in disc


def test_artifact_no_api_key_leak() -> None:
    art = _load("v38_4_verdict.json")
    assert "sk-or-v1" not in json.dumps(art)


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v38_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "granite_score", "deepseek_score", "routing_score",
        "governance_identity", "hallucination_containment",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v38_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == "LIVE_LLM_VALIDATION_PASSED"
    assert art["classification"] == (
        "live_validated_epistemic_governance_system"
    )
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v38_4_verdict.json")
    assert art == build_verdict_artifact()


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_live_llm_validation_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_realness_and_safety() -> None:
    doc = _read("desi_live_llm_validation_go_no_go.md")
    assert "echte" in doc
    assert "kein API-Key liegt im Repo" in doc
    assert "HUMAN_APPROVAL_REQUIRED" in doc


def test_go_no_go_no_key_leak() -> None:
    assert "sk-or-v1" not in _read(
        "desi_live_llm_validation_go_no_go.md"
    )


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_live_llm_validation_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_live_llm_validation_go_no_go.md")
    assert doc == build_go_no_go()
