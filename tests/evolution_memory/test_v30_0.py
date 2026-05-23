"""v30.0 - Mutation Memory Topology tests."""
from __future__ import annotations

import json
import pathlib

from desi.evolution_memory import (
    DECISION_REJECT, EDGE_TYPES, NODE_TYPES, accepted_mutations,
    allowed_triples, build_report, build_topology_artifact,
    decision_for, decision_visibility, decisions, edges,
    evolution_traceability, invalid_edges, lineage_visibility,
    mutation_edge_kinds, mutations, nodes, rejected_mutations,
    rejection_visibility, replay_stability,
)
from desi.evolution_memory.report import (
    REPORT_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "evolution_memory"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- closed schema ------------------------------
def test_node_and_edge_types() -> None:
    assert len(NODE_TYPES) == 12
    assert len(EDGE_TYPES) == 10


def test_no_invalid_edges() -> None:
    assert invalid_edges() == ()


def test_every_edge_matches_allowed_triple() -> None:
    types = {n.node_id: n.node_type for n in nodes()}
    allowed = set(allowed_triples())
    for e in edges():
        assert (
            types[e.source], e.edge_type, types[e.target],
        ) in allowed


# --- mutations: accepted AND rejected kept ------
def test_mutations_split() -> None:
    assert len(mutations()) >= 1
    assert len(accepted_mutations()) >= 1
    assert len(rejected_mutations()) >= 1
    assert (
        len(accepted_mutations()) + len(rejected_mutations())
        == len(mutations())
    )


def test_rejected_ideas_preserved_with_reasons() -> None:
    # rejected ideas are kept as nodes with a reason + invariant
    for m in rejected_mutations():
        kinds = mutation_edge_kinds(m.mutation_id)
        assert "REJECTED_BECAUSE" in kinds
        assert "INVALIDATED_BY" in kinds
        d = decision_for(m.mutation_id)
        assert d.outcome == DECISION_REJECT
        assert d.reason
        assert d.invariant


# --- the five Pflichtmetriken -------------------
def test_lineage_visibility_full() -> None:
    assert lineage_visibility() == 1.0


def test_decision_visibility_full() -> None:
    assert decision_visibility() == 1.0
    assert len(decisions()) == len(mutations())


def test_rejection_visibility_full() -> None:
    assert rejection_visibility() == 1.0


def test_evolution_traceability_full() -> None:
    assert evolution_traceability() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        lineage_visibility(), decision_visibility(),
        rejection_visibility(), evolution_traceability(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_structured() -> None:
    assert build_report().recommendation == VERDICT_STRUCTURED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v30_0_topology.json")
    assert art["schema_version"] == (
        "v30_0_mutation_memory_topology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v30_0_topology.json")
    disc = art["disclaimer"].lower()
    assert "never deleted" in disc
    assert "no implicit learning" in disc
    assert "not a learning layer" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v30_0_topology.json")
    required = {
        "lineage_visibility", "decision_visibility",
        "rejection_visibility", "evolution_traceability",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v30_0_topology.json")
    live = build_topology_artifact()
    assert art == live
