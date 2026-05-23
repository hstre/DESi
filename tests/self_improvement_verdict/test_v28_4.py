"""v28.4 - Self-Improvement Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.self_improvement_verdict import (
    GATE_PASS_STATEMENT, SELF_IMPROVEMENT_CLASSES,
    SelfImprovementClass, aggregate, authority_resistance,
    build_go_no_go, build_report, build_verdict_artifact,
    class_meaning, class_rank, classify_corpus, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    human_approval_enforcement, is_acceptable,
)
from desi.self_improvement_verdict.report import (
    REPORT_VERDICTS, VERDICT_GOVERNED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "self_improvement"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert SELF_IMPROVEMENT_CLASSES == tuple(
        c.value for c in SelfImprovementClass
    )
    assert len(SELF_IMPROVEMENT_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in SELF_IMPROVEMENT_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        SelfImprovementClass.A_CONTROLLED_EVOLUTIONARY.value
    ) > class_rank(
        SelfImprovementClass.E_EPISTEMICALLY_UNSAFE.value
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(
        SelfImprovementClass.A_CONTROLLED_EVOLUTIONARY.value
    )
    assert is_acceptable(
        SelfImprovementClass.C_PRODUCTIVE_UNSTABLE.value
    )
    assert not is_acceptable(
        SelfImprovementClass.D_AUTHORITY_DRIFTING.value
    )
    assert not is_acceptable(
        SelfImprovementClass.E_EPISTEMICALLY_UNSAFE.value
    )


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["replay_integrity"].value >= 0.95
    assert by["governance_preservation"].value >= 0.95
    assert by["unsafe_containment"].value >= 0.95
    assert by["branch_isolation"].value >= 1.0
    assert by["human_approval_enforcement"].value == 1.0
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "menschlicher Governance" in r.gate_statement


# --- human approval enforced --------------------
def test_human_approval_enforcement_full() -> None:
    assert human_approval_enforcement() == 1.0


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.replay_integrity, m.governance_preservation,
        m.unsafe_containment, m.branch_isolation,
        m.human_approval_enforcement, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


def test_authority_resistance_high() -> None:
    assert authority_resistance() >= 0.95


# --- classification -----------------------------
def test_corpus_class_controlled_evolutionary() -> None:
    assert classify_corpus() == (
        SelfImprovementClass.A_CONTROLLED_EVOLUTIONARY.value
    )


def test_corpus_not_drifting_or_unsafe() -> None:
    bad = {
        SelfImprovementClass.D_AUTHORITY_DRIFTING.value,
        SelfImprovementClass.E_EPISTEMICALLY_UNSAFE.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in SELF_IMPROVEMENT_CLASSES:
        assert class_meaning(c).strip()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_governed() -> None:
    assert build_report().recommendation == VERDICT_GOVERNED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v28_4_verdict.json")
    assert art["schema_version"] == (
        "v28_4_self_improvement_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v28_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "never autonomous self-modification" in disc
    assert "nothing is applied" in disc
    assert "human_approval is mandatory" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v28_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "replay_integrity", "governance_preservation",
        "unsafe_containment", "branch_isolation",
        "human_approval_enforcement", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v28_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "CONTROLLED_SELF_IMPROVEMENT_GOVERNED"
    )
    assert art["classification"] == (
        "controlled_evolutionary_governance"
    )
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v28_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_self_improvement_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_human_approval_and_no_autonomy() -> None:
    doc = _read("desi_self_improvement_go_no_go.md")
    assert "HUMAN_APPROVAL_REQUIRED" in doc
    assert "autonome Selbstverbesserung" in doc
    assert "Kein automatisches Merge" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_self_improvement_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_self_improvement_go_no_go.md")
    assert doc == build_go_no_go()
