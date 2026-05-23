"""v25.2 - Citation & Reference Governance tests."""
from __future__ import annotations

import json
import pathlib

from desi.output_ports_citation import (
    CitationEdge, build_citation_governance_artifact,
    build_report, citation_edges, citation_traceability,
    claim_reference_alignment, detects_synthetic_phantom,
    is_phantom_ref, is_registered, missing_citations,
    orphan_references, phantom_citation_detection,
    phantom_citations, reference_usage_integrity, references,
    replay_stability, unsupported_related_work_claims,
    wrong_reference_assignment,
)
from desi.output_ports_citation.report import (
    REPORT_VERDICTS, VERDICT_EDGES,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "output_ports"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- citations are edges ------------------------
def test_citation_edges_built() -> None:
    edges = citation_edges()
    assert len(edges) >= 1
    for e in edges:
        assert e.claim_id
        assert e.ref_key


def test_single_reference_registry() -> None:
    # the registry is the v25.1 one, not a divergent copy
    from desi.output_ports_arxiv import references as src_refs
    assert {r.ref_key for r in references()} == {
        r.ref_key for r in src_refs()
    }


# --- phantom detection --------------------------
def test_phantom_citation_detection_full() -> None:
    assert phantom_citation_detection() == 1.0


def test_no_real_phantoms() -> None:
    assert phantom_citations() == ()


def test_detector_flags_synthetic_phantom() -> None:
    assert detects_synthetic_phantom() is True
    assert is_phantom_ref("___not_registered___") is True
    assert is_phantom_ref("rentschler_roberts_2025") is False


# --- alignment / usage / traceability -----------
def test_claim_reference_alignment_full() -> None:
    assert claim_reference_alignment() == 1.0


def test_reference_usage_integrity_full() -> None:
    assert reference_usage_integrity() == 1.0


def test_citation_traceability_full() -> None:
    assert citation_traceability() == 1.0


def test_no_missing_or_orphan_or_misassigned() -> None:
    assert missing_citations() == ()
    assert orphan_references() == ()
    assert wrong_reference_assignment() == ()
    assert unsupported_related_work_claims() == ()


def test_every_cited_ref_is_registered() -> None:
    for e in citation_edges():
        assert is_registered(e.ref_key)


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        phantom_citation_detection(),
        claim_reference_alignment(),
        reference_usage_integrity(), citation_traceability(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_edges() -> None:
    assert build_report().recommendation == VERDICT_EDGES


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v25_2_citation_governance.json")
    assert art["schema_version"] == "v25_2_citation_governance"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v25_2_citation_governance.json")
    disc = art["disclaimer"].lower()
    assert "epistemic edge" in disc or "directed edges" in disc
    assert "not as literature decoration" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v25_2_citation_governance.json")
    required = {
        "phantom_citation_detection",
        "claim_reference_alignment",
        "reference_usage_integrity", "citation_traceability",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v25_2_citation_governance.json")
    live = build_citation_governance_artifact()
    assert art == live
