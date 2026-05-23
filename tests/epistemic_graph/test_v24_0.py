"""v24.0 - Epistemic Graph Schema tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_graph import (
    EDGE_TYPES, NODE_TYPES, Edge, EdgeType, Node, NodeType,
    allowed_triples, build_report, build_schema_artifact,
    claim_lineage_visible, conflict_visibility,
    determinism_signatures, edges, edges_of_type,
    graph_determinism, graph_signature, invalid_edges,
    is_valid_triple, lineage_visibility, nodes, nodes_of_type,
    replay_stability, required_edge_types, required_node_types,
    schema_coverage, schema_signature,
)
from desi.epistemic_graph.report import (
    REPORT_VERDICTS, VERDICT_EXPLICIT,
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


# --- closed taxonomies --------------------------
def test_node_types_closed() -> None:
    assert NODE_TYPES == tuple(t.value for t in NodeType)
    assert len(NODE_TYPES) == 11


def test_edge_types_closed() -> None:
    assert EDGE_TYPES == tuple(t.value for t in EdgeType)
    assert len(EDGE_TYPES) == 9


def test_node_rejects_unknown_type() -> None:
    try:
        Node("x", "NotAType", "label")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_edge_rejects_unknown_type() -> None:
    try:
        Edge("a", "b", "NOT_AN_EDGE")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


# --- schema coverage ----------------------------
def test_schema_coverage_full() -> None:
    assert schema_coverage() == 1.0


def test_all_node_types_present() -> None:
    present = {n.node_type for n in nodes()}
    assert present == set(required_node_types())


def test_all_edge_types_present() -> None:
    present = {e.edge_type for e in edges()}
    assert present == set(required_edge_types())


# --- schema validity ----------------------------
def test_no_invalid_edges() -> None:
    assert invalid_edges() == ()


def test_every_edge_matches_an_allowed_triple() -> None:
    types = {n.node_id: n.node_type for n in nodes()}
    allowed = set(allowed_triples())
    for e in edges():
        triple = (types[e.source], e.edge_type, types[e.target])
        assert triple in allowed


def test_is_valid_triple() -> None:
    assert is_valid_triple("Claim", "GENERATED_IN", "Sprint")
    assert not is_valid_triple("Sprint", "GENERATED_IN", "Claim")


def test_all_edge_endpoints_exist() -> None:
    ids = {n.node_id for n in nodes()}
    for e in edges():
        assert e.source in ids
        assert e.target in ids


# --- lineage ------------------------------------
def test_lineage_visibility_full() -> None:
    assert lineage_visibility() == 1.0


def test_every_claim_has_visible_lineage() -> None:
    for c in nodes_of_type(NodeType.CLAIM.value):
        claim_id = c.node_id.split(":", 1)[1]
        assert claim_lineage_visible(claim_id)


def test_claims_are_grounded_in_live_layer() -> None:
    from desi.icrl_followup_revision import claims
    claim_ids = {
        c.node_id.split(":", 1)[1]
        for c in nodes_of_type(NodeType.CLAIM.value)
    }
    assert claim_ids == {c.claim_id for c in claims()}


# --- conflicts ----------------------------------
def test_conflict_visibility_full() -> None:
    assert conflict_visibility() == 1.0


def test_conflicts_are_modelled() -> None:
    assert len(edges_of_type("CONFLICTS_WITH")) >= 1
    assert len(nodes_of_type(NodeType.DISSENT_PATH.value)) >= 1


# --- determinism / replay -----------------------
def test_graph_determinism_one() -> None:
    assert graph_determinism() == 1.0
    a, b = determinism_signatures()
    assert a == b


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_graph_signature_stable() -> None:
    assert graph_signature() == graph_signature()
    assert schema_signature() == schema_signature()


def test_metrics_in_unit_interval() -> None:
    for m in (
        schema_coverage(), lineage_visibility(),
        conflict_visibility(), graph_determinism(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_explicit() -> None:
    assert build_report().recommendation == VERDICT_EXPLICIT


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- the read-only / canonical guarantee --------
def test_graph_does_not_recompute_values() -> None:
    """Metric nodes carry only the metric name as label, never
    a recomputed numeric value - values stay canonical in the
    JSON artifacts."""
    for m in nodes_of_type(NodeType.METRIC.value):
        assert m.label == m.node_id.split(":", 1)[1]


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v24_0_schema.json")
    assert art["schema_version"] == (
        "v24_0_epistemic_graph_schema"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v24_0_schema.json")
    disc = art["disclaimer"].lower()
    assert "read-only" in disc
    assert "canonical" in disc
    assert "ranks nothing" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v24_0_schema.json")
    required = {
        "schema_coverage", "lineage_visibility",
        "conflict_visibility", "graph_determinism",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v24_0_schema.json")
    live = build_schema_artifact()
    assert art == live
