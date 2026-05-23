"""v25.1 - arXiv Paper Port tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.output_ports import schema_for, PortType
from desi.output_ports_arxiv import (
    base_paper_cited, build_arxiv_artifact, build_report,
    citation_completeness, external_claims,
    metric_definition_coverage, missing_sections,
    paper_forbidden_hits, phantom_citations, references, render,
    replay_stability, required_sections,
    result_derivation_visibility, result_lines,
    section_completeness, unreferenced_external_claims,
    unused_references,
)
from desi.output_ports_arxiv.report import (
    REPORT_VERDICTS, VERDICT_TRACEABLE,
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


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- section completeness -----------------------
def test_section_completeness_full() -> None:
    assert section_completeness() == 1.0
    assert missing_sections() == ()


def test_required_sections_match_schema() -> None:
    assert required_sections() == (
        schema_for(PortType.ARXIV_PAPER.value).required_sections
    )
    assert len(required_sections()) == 13


def test_rendered_paper_has_all_sections() -> None:
    from desi.output_ports import section_title
    paper = render()
    for key in required_sections():
        if key == "title":
            continue
        assert section_title(key) in paper


# --- citation completeness ----------------------
def test_citation_completeness_full() -> None:
    assert citation_completeness() == 1.0


def test_base_paper_cited() -> None:
    assert base_paper_cited() is True
    assert "arXiv:2501.14176" in render()
    assert "Rentschler and Roberts" in render()


def test_no_phantom_citations() -> None:
    assert phantom_citations() == ()


def test_no_unreferenced_external_claims() -> None:
    assert unreferenced_external_claims() == ()


def test_no_unused_references() -> None:
    assert unused_references() == ()


def test_every_external_claim_has_reference() -> None:
    for c in external_claims():
        assert c.reference_keys


# --- metric definitions & derivations -----------
def test_metric_definition_coverage_full() -> None:
    assert metric_definition_coverage() == 1.0


def test_result_derivation_visibility_full() -> None:
    assert result_derivation_visibility() == 1.0


def test_no_naked_numbers() -> None:
    for line in result_lines():
        assert line.is_derived()
        assert line.sprint_source


def test_results_match_live_layer() -> None:
    from desi.icrl_followup_conditions import by_result_id
    by_metric = {l.metric_name: l.value for l in result_lines()}
    assert by_metric["redundancy_reduction"] == round(
        by_result_id("R1").value, 6
    )
    assert by_metric["productivity_gain"] == round(
        by_result_id("R7").value, 6
    )


# --- governance ---------------------------------
def test_paper_has_no_forbidden_terms() -> None:
    assert paper_forbidden_hits() == ()
    assert forbidden_hits(render()) == ()


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_paper_render_is_stable() -> None:
    assert render() == render()


def test_metrics_in_unit_interval() -> None:
    for m in (
        section_completeness(), citation_completeness(),
        metric_definition_coverage(),
        result_derivation_visibility(), replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_traceable() -> None:
    assert build_report().recommendation == VERDICT_TRACEABLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v25_1_arxiv_port.json")
    assert art["schema_version"] == "v25_1_arxiv_paper_port"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v25_1_arxiv_port.json")
    disc = art["disclaimer"].lower()
    assert "provenance-bound export" in disc
    assert "not free text generation" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v25_1_arxiv_port.json")
    required = {
        "section_completeness", "citation_completeness",
        "metric_definition_coverage",
        "result_derivation_visibility", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v25_1_arxiv_port.json")
    live = build_arxiv_artifact()
    assert art == live


# --- rendered deliverable -----------------------
def test_rendered_paper_present_and_matches() -> None:
    paper = _read("arxiv_port_rendered_paper.md")
    assert paper == render()
    assert "Section 4.6" in paper
    assert forbidden_hits(paper) == ()
