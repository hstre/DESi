"""v24.3 - Graph Query & Scientific Rendering tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.epistemic_graph_queries import (
    build_queries_artifact, build_report, citations,
    claim_citation, claim_ids, condition_reconstruction,
    fixtures_of, generating_sprints, has_cycle,
    has_dangling_edges, is_traceable, limitations_of,
    lineage_integrity, methods_of, metric_citation,
    metric_derivation_visibility, metric_names,
    metric_replay_hashes, metric_sprints,
    metric_supported_claims, paper_lineage, provenance_of,
    references_section, replay_hashes_of, replay_stability,
    scientific_traceability, section_forbidden_hits,
    supporting_metrics, trace_records, traceability_section,
)
from desi.epistemic_graph_queries.report import (
    REPORT_VERDICTS, VERDICT_AUTO,
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


# --- read-only queries reflect the live layer ---
def test_claims_match_live_layer() -> None:
    from desi.icrl_followup_revision import claims
    assert set(claim_ids()) == {c.claim_id for c in claims()}


def test_provenance_is_structured() -> None:
    for c in claim_ids():
        p = provenance_of(c)
        assert set(p.keys()) == {
            "claim_id", "sprints", "methods", "fixtures",
            "replay_hashes", "limitations", "governance",
            "metrics",
        }


# --- scientific traceability --------------------
def test_scientific_traceability_full() -> None:
    assert scientific_traceability() == 1.0


def test_every_claim_traceable() -> None:
    for c in claim_ids():
        assert is_traceable(c)
        assert generating_sprints(c)
        assert methods_of(c) or fixtures_of(c)
        assert replay_hashes_of(c)
        assert limitations_of(c)


def test_trace_records_complete() -> None:
    for r in trace_records():
        assert r.is_complete()


# --- metric derivation --------------------------
def test_metric_derivation_visibility_full() -> None:
    assert metric_derivation_visibility() == 1.0


def test_every_metric_derivation_visible() -> None:
    for m in metric_names():
        assert metric_sprints(m)
        assert metric_supported_claims(m)
        assert metric_replay_hashes(m)


# --- condition reconstruction -------------------
def test_condition_reconstruction_full() -> None:
    assert condition_reconstruction() == 1.0


# --- lineage integrity --------------------------
def test_lineage_integrity_full() -> None:
    assert lineage_integrity() == 1.0


def test_graph_is_clean_dag() -> None:
    assert has_dangling_edges() is False
    assert has_cycle() is False


def test_paper_lineage_links_artifacts_to_sprints() -> None:
    lineage = paper_lineage()
    assert len(lineage) >= 1
    for entry in lineage:
        assert entry["sprint"] is not None


# --- citations ----------------------------------
def test_citations_cover_claims_and_metrics() -> None:
    assert len(citations()) == len(claim_ids()) + len(metric_names())
    kinds = {c.kind for c in citations()}
    assert kinds == {"claim", "metric"}


def test_citation_text_carries_sprint() -> None:
    for c in claim_ids():
        cit = claim_citation(c)
        for sp in generating_sprints(c):
            assert sp in cit.text


# --- governance still applies to rendering ------
def test_rendering_has_no_forbidden_terms() -> None:
    assert section_forbidden_hits() == ()
    assert forbidden_hits(traceability_section()) == ()
    assert forbidden_hits(references_section()) == ()


# --- metrics in range ---------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        scientific_traceability(), metric_derivation_visibility(),
        condition_reconstruction(), lineage_integrity(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_auto_derived() -> None:
    assert build_report().recommendation == VERDICT_AUTO


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v24_3_queries.json")
    assert art["schema_version"] == "v24_3_graph_queries"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v24_3_queries.json")
    disc = art["disclaimer"].lower()
    assert "read-only" in disc
    assert "not decisions" in disc
    assert "canonical" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v24_3_queries.json")
    required = {
        "scientific_traceability",
        "metric_derivation_visibility",
        "condition_reconstruction", "lineage_integrity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v24_3_queries.json")
    live = build_queries_artifact()
    assert art == live
