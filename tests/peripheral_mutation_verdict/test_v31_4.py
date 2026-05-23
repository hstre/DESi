"""v31.4 - Peripheral Mutation Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.peripheral_mutation_verdict import (
    GATE_PASS_STATEMENT, MUTATION_CLASSES, MutationClass, aggregate,
    build_go_no_go, build_report, build_verdict_artifact,
    class_meaning, class_rank, classify_corpus, core_identity,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    governance_identity, human_approval_enforcement, is_acceptable,
    lineage_integrity, mutation_traceability, replay_integrity,
)
from desi.peripheral_mutation_verdict.report import (
    REPORT_VERDICTS, VERDICT_VALIDATED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "peripheral_mutation"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert MUTATION_CLASSES == tuple(c.value for c in MutationClass)
    assert len(MUTATION_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in MUTATION_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(
        MutationClass.A_STABLE_PERIPHERAL_EVOLUTION.value
    ) > class_rank(
        MutationClass.E_EPISTEMICALLY_UNSTABLE.value
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(
        MutationClass.A_STABLE_PERIPHERAL_EVOLUTION.value
    )
    assert is_acceptable(
        MutationClass.C_PRODUCTIVE_DRIFTING.value
    )
    assert not is_acceptable(
        MutationClass.D_HIDDEN_CORE_EROSION.value
    )
    assert not is_acceptable(
        MutationClass.E_EPISTEMICALLY_UNSTABLE.value
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
    assert by["core_identity"].value == 1.0
    assert by["governance_identity"].value == 1.0
    assert by["lineage_integrity"].value >= 0.95
    assert by["human_approval_enforcement"].value == 1.0
    assert by["mutation_traceability"].value >= 0.95


def test_core_and_governance_identity_full() -> None:
    assert core_identity() == 1.0
    assert governance_identity() == 1.0


def test_human_approval_enforcement_full() -> None:
    assert human_approval_enforcement() == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "geschuetzten Kerns" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.replay_integrity, m.core_identity,
        m.governance_identity, m.lineage_integrity,
        m.human_approval_enforcement, m.mutation_traceability,
    ):
        assert 0.0 <= v <= 1.0


def test_metric_helpers_consistent() -> None:
    m = aggregate()
    assert m.replay_integrity == replay_integrity()
    assert m.lineage_integrity == lineage_integrity()
    assert m.mutation_traceability == mutation_traceability()


# --- classification -----------------------------
def test_corpus_class_stable_peripheral() -> None:
    assert classify_corpus() == (
        MutationClass.A_STABLE_PERIPHERAL_EVOLUTION.value
    )


def test_corpus_not_eroded_or_unstable() -> None:
    bad = {
        MutationClass.D_HIDDEN_CORE_EROSION.value,
        MutationClass.E_EPISTEMICALLY_UNSTABLE.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in MUTATION_CLASSES:
        assert class_meaning(c).strip()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
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


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v31_4_verdict.json")
    assert art["schema_version"] == (
        "v31_4_peripheral_mutation_verdict"
    )


def test_artifact_is_branch_isolated() -> None:
    art = _load("v31_4_verdict.json")
    assert art["branch"] == "proposal/peripheral_mutation_v1"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v31_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "real, branch-isolated" in disc
    assert "byte-identical" in disc
    assert "no core module is touched" in disc
    assert "nothing is merged" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v31_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "replay_integrity", "core_identity",
        "governance_identity", "lineage_integrity",
        "human_approval_enforcement", "mutation_traceability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v31_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "PERIPHERAL_MUTATION_REPLAY_VALIDATED"
    )
    assert art["classification"] == "stable_peripheral_evolution"
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v31_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_peripheral_mutation_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_safety_rule() -> None:
    doc = _read("desi_peripheral_mutation_go_no_go.md")
    assert "HUMAN_APPROVAL_REQUIRED" in doc
    assert "FORBIDDEN_CORE_MUTATION" in doc
    assert "byte-identisch" in doc


def test_go_no_go_lists_protected_core() -> None:
    doc = _read("desi_peripheral_mutation_go_no_go.md")
    assert "Replay Kernel" in doc
    assert "Determinism Scanner" in doc
    assert "Governance Core" in doc


def test_go_no_go_has_no_forbidden_terms() -> None:
    assert forbidden_hits(
        _read("desi_peripheral_mutation_go_no_go.md")
    ) == ()


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_peripheral_mutation_go_no_go.md")
    assert doc == build_go_no_go()
