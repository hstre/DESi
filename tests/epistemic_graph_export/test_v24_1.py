"""v24.1 - Neo4j Export Layer tests.

None of these tests require a live Neo4j. They run entirely
against the offline DryRunClient, proving DESi exports
deterministically with the `neo4j` package absent.
"""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_graph import edges, graph_signature, nodes
from desi.epistemic_graph_export import (
    DryRunClient, Neo4jUnavailableError, build_export_artifact,
    build_report, canonical_preservation, connect,
    cypher_statements, export, export_determinism,
    export_payload, from_projection, governance_independence,
    graph_consistency, neo4j_available, project,
    projection_signature, replay_integrity,
    round_trip_signature, statements_signature,
)
from desi.epistemic_graph_export.report import (
    REPORT_VERDICTS, VERDICT_SAFE,
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


# --- Neo4j is optional, never required ----------
def test_module_imports_without_neo4j() -> None:
    # neo4j_available returns a bool either way; import worked.
    assert isinstance(neo4j_available(), bool)


def test_dry_run_client_records_statements() -> None:
    c = DryRunClient()
    export(c)
    assert len(c.executed()) == len(cypher_statements())
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


# --- determinism --------------------------------
def test_export_determinism_one() -> None:
    assert export_determinism() == 1.0


def test_statements_signature_stable() -> None:
    assert statements_signature() == statements_signature()


def test_export_is_idempotent_in_statements() -> None:
    a = [s for s, _ in DryRunClient().executed()]
    c1, c2 = DryRunClient(), DryRunClient()
    export(c1)
    export(c2)
    assert c1.executed() == c2.executed()


def test_statement_count_matches_graph() -> None:
    assert len(cypher_statements()) == len(nodes()) + len(edges())


# --- canonical preservation ---------------------
def test_canonical_preservation_one() -> None:
    assert canonical_preservation() == 1.0


def test_round_trip_reconstructs_graph() -> None:
    assert round_trip_signature() == graph_signature()
    assert projection_signature() == graph_signature()


def test_export_does_not_mutate_graph() -> None:
    before = graph_signature()
    export(DryRunClient())
    assert graph_signature() == before


def test_from_projection_matches_nodes_edges() -> None:
    n2, e2 = from_projection(project())
    assert set(n2) == set(nodes())
    assert set(e2) == set(edges())


# --- replay integrity ---------------------------
def test_replay_integrity_one() -> None:
    assert replay_integrity() == 1.0


# --- graph consistency --------------------------
def test_graph_consistency_one() -> None:
    assert graph_consistency() == 1.0


# --- governance independence --------------------
def test_governance_independence_one() -> None:
    assert governance_independence() >= 0.95


def test_governance_unchanged_by_export() -> None:
    from desi.scientific_rendering import forbidden_hits
    before = forbidden_hits("AGI breakthrough")
    export(DryRunClient())
    after = forbidden_hits("AGI breakthrough")
    assert before == after


# --- metrics in range ---------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        export_determinism(), canonical_preservation(),
        replay_integrity(), graph_consistency(),
        governance_independence(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_safe() -> None:
    assert build_report().recommendation == VERDICT_SAFE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- payload ------------------------------------
def test_export_payload_keys() -> None:
    p = export_payload()
    assert set(p.keys()) == {
        "projection", "cypher", "statements_signature",
        "round_trip_signature",
    }
    assert len(p["cypher"]) == len(cypher_statements())


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v24_1_export.json")
    assert art["schema_version"] == "v24_1_neo4j_export"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v24_1_export.json")
    disc = art["disclaimer"].lower()
    assert "read-only" in disc
    assert "optional" in disc
    assert "reads nothing back" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v24_1_export.json")
    required = {
        "export_determinism", "canonical_preservation",
        "replay_integrity", "graph_consistency",
        "governance_independence",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v24_1_export.json")
    live = build_export_artifact()
    assert art == live
