"""v27.1 - Claim Graph & Neo4j Integration tests.

No test requires a live Neo4j; the projection runs against the
offline DryRunClient.
"""
from __future__ import annotations

import json
import pathlib

from desi.research_claim_graph import (
    EDGE_TYPES, NODE_TYPES, DryRunClient, Neo4jUnavailableError,
    NodeType, allowed_triples, build_graph_artifact,
    build_report, conflict_visibility, connect,
    cypher_statements, edges, edges_of_type, graph_connectivity,
    graph_signature, has_cycle, has_dangling_edges,
    invalid_edges, is_valid_triple, lineage_integrity,
    neo4j_available, nodes, nodes_of_type,
    open_problem_visibility, project, replay_stability,
)
from desi.research_claim_graph.report import (
    REPORT_VERDICTS, VERDICT_GRAPHED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "research_harvester"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- closed taxonomies --------------------------
def test_node_types_count() -> None:
    assert len(NODE_TYPES) == 8


def test_edge_types_count() -> None:
    assert len(EDGE_TYPES) == 9


def test_all_node_and_edge_types_present() -> None:
    assert {n.node_type for n in nodes()} == set(NODE_TYPES)
    assert {e.edge_type for e in edges()} == set(EDGE_TYPES)


# --- schema validity ----------------------------
def test_no_invalid_edges() -> None:
    assert invalid_edges() == ()


def test_every_edge_matches_allowed_triple() -> None:
    types = {n.node_id: n.node_type for n in nodes()}
    allowed = set(allowed_triples())
    for e in edges():
        assert (
            types[e.source], e.edge_type, types[e.target],
        ) in allowed


def test_endpoints_exist() -> None:
    ids = {n.node_id for n in nodes()}
    for e in edges():
        assert e.source in ids and e.target in ids


# --- connectivity / conflicts / open problems ---
def test_graph_connectivity_full() -> None:
    assert graph_connectivity() == 1.0


def test_conflict_visibility_full() -> None:
    assert conflict_visibility() == 1.0
    assert len(edges_of_type("CONFLICTS_WITH")) >= 1


def test_open_problem_visibility_full() -> None:
    assert open_problem_visibility() == 1.0
    assert len(nodes_of_type(NodeType.OPEN_QUESTION.value)) >= 1


def test_lineage_integrity_full() -> None:
    assert lineage_integrity() == 1.0
    assert has_dangling_edges() is False
    assert has_cycle() is False


def test_is_valid_triple() -> None:
    assert is_valid_triple("Paper", "CLAIMS", "Claim")
    assert not is_valid_triple("Claim", "CLAIMS", "Paper")


# --- Neo4j optional, read-only ------------------
def test_neo4j_optional() -> None:
    assert isinstance(neo4j_available(), bool)


def test_projection_runs_offline() -> None:
    c = DryRunClient()
    n = project(c)
    assert n == len(cypher_statements())
    assert len(c.executed()) == n
    assert c.read_only_from_desi is True


def test_connect_raises_without_neo4j() -> None:
    if neo4j_available():
        return
    try:
        connect("bolt://localhost:7687", "neo4j", "x")
    except Neo4jUnavailableError:
        pass
    else:
        raise AssertionError("expected Neo4jUnavailableError")


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_graph_signature_stable() -> None:
    assert graph_signature() == graph_signature()


def test_metrics_in_unit_interval() -> None:
    for m in (
        graph_connectivity(), conflict_visibility(),
        open_problem_visibility(), lineage_integrity(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- no ranking ---------------------------------
def test_no_ranking_fields() -> None:
    d = build_report().to_dict()
    forbidden = {"score", "rank", "ranking", "impact", "best"}
    assert forbidden.isdisjoint(set(d.keys()))


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_graphed() -> None:
    assert build_report().recommendation == VERDICT_GRAPHED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v27_1_graph.json")
    assert art["schema_version"] == "v27_1_claim_graph"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v27_1_graph.json")
    disc = art["disclaimer"].lower()
    assert "read-only" in disc
    assert "ranks nothing" in disc
    assert "never adjudicated" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v27_1_graph.json")
    required = {
        "graph_connectivity", "conflict_visibility",
        "open_problem_visibility", "lineage_integrity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v27_1_graph.json")
    live = build_graph_artifact()
    assert art == live
