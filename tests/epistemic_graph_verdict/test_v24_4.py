"""v24.4 - Epistemic Graph Verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_graph_verdict import (
    GATE_PASS_STATEMENT, GRAPH_CLASSES, GraphClass, aggregate,
    build_go_no_go, build_graph_verdict_artifact, build_report,
    class_meaning, class_rank, classify_corpus, gate_conditions,
    gate_failing_conditions, gate_passes_all, is_acceptable,
)
from desi.epistemic_graph_verdict.report import (
    REPORT_VERDICTS, VERDICT_GOVERNED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "epistemic_graph"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- closed taxonomy ----------------------------
def test_classes_closed_set() -> None:
    assert GRAPH_CLASSES == tuple(c.value for c in GraphClass)
    assert len(GRAPH_CLASSES) == 5


def test_class_rank_ordering() -> None:
    ranks = [class_rank(c) for c in GRAPH_CLASSES]
    assert len(set(ranks)) == 5
    assert class_rank(GraphClass.A_REPLAY_GOVERNED.value) > (
        class_rank(GraphClass.E_FRAGMENTED.value)
    )


def test_acceptable_classes() -> None:
    assert is_acceptable(GraphClass.A_REPLAY_GOVERNED.value)
    assert is_acceptable(GraphClass.C_CONFLICT_RICH_STABLE.value)
    assert not is_acceptable(GraphClass.D_STALE_DRIFTED.value)
    assert not is_acceptable(GraphClass.E_FRAGMENTED.value)


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["replay_integrity"].value >= 0.95
    assert by["lineage_visibility"].value >= 0.90
    assert by["cache_validity"].value >= 0.90
    assert by["traceability"].value >= 0.90
    assert by["governance_independence"].value >= 0.95
    assert by["replay_stability"].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "ohne versteckte" in r.gate_statement


# --- metrics ------------------------------------
def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.replay_integrity, m.lineage_visibility,
        m.cache_validity, m.traceability,
        m.governance_independence, m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


# --- classification -----------------------------
def test_corpus_class_replay_governed() -> None:
    assert classify_corpus() == (
        GraphClass.A_REPLAY_GOVERNED.value
    )


def test_corpus_not_drifted_or_fragmented() -> None:
    bad = {
        GraphClass.D_STALE_DRIFTED.value,
        GraphClass.E_FRAGMENTED.value,
    }
    assert classify_corpus() not in bad


def test_class_meaning_for_every_class() -> None:
    for c in GRAPH_CLASSES:
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
    art = _load("v24_4_verdict.json")
    assert art["schema_version"] == (
        "v24_4_epistemic_graph_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v24_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "read-only" in disc
    assert "no agent soul" in disc
    assert "canonical" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v24_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "replay_integrity", "lineage_visibility",
        "cache_validity", "traceability",
        "governance_independence", "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v24_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "EPISTEMIC_MEMORY_REPLAY_GOVERNED"
    )
    assert art["classification"] == "replay_governed_graph"


def test_artifact_full_matches_live_build() -> None:
    art = _load("v24_4_verdict.json")
    live = build_graph_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_present() -> None:
    doc = _read("desi_epistemic_graph_go_no_go.md")
    assert "Killerfrage" in doc
    assert "Concept Gate" in doc
    assert GATE_PASS_STATEMENT in doc


def test_go_no_go_states_read_only_rule() -> None:
    doc = _read("desi_epistemic_graph_go_no_go.md")
    assert "read-only" in doc
    # no test may depend on a running Neo4j instance
    assert "Neo4j-Instanz" in doc
    assert "Ohne Neo4j funktioniert DESi" in doc
    assert "Keine" in doc  # refusal section


def test_go_no_go_matches_live_build() -> None:
    doc = _read("desi_epistemic_graph_go_no_go.md")
    assert doc == build_go_no_go()
