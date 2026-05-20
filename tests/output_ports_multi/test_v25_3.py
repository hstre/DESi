"""v25.3 - Multi-Port Rendering tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.output_ports import PORT_TYPES, schema_for, section_title
from desi.output_ports_multi import (
    all_renders, build_multi_port_artifact, build_report,
    canonical_body, corpus_forbidden_hits,
    cross_port_claim_consistency, cross_port_metric_consistency,
    format_validity, limitation_preservation, render_port,
    render_citation_appendix, render_reproducibility_statement,
    render_technical_report, render_workshop_note,
    replay_stability,
)
from desi.output_ports_multi.report import (
    REPORT_VERDICTS, VERDICT_PUBLISHABLE,
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


# --- cross-port consistency ---------------------
def test_cross_port_claim_consistency_full() -> None:
    assert cross_port_claim_consistency() == 1.0


def test_cross_port_metric_consistency_full() -> None:
    assert cross_port_metric_consistency() == 1.0


def test_shared_section_bodies_identical_across_ports() -> None:
    # any section both arxiv and technical report include must
    # render byte-identically
    arxiv = set(schema_for("arxiv_paper_port").required_sections)
    tech = set(
        schema_for("technical_report_port").required_sections
    )
    shared = (arxiv & tech) - {"title"}
    for sec in shared:
        body = canonical_body(sec)
        assert body in render_port("arxiv_paper_port")
        assert body in render_port("technical_report_port")


def test_numbers_identical_across_result_ports() -> None:
    from desi.output_ports_arxiv import result_lines
    ports = [
        p for p in PORT_TYPES
        if "results" in schema_for(p).required_sections
    ]
    for line in result_lines():
        for p in ports:
            assert str(line.value) in render_port(p)


# --- format validity & differences --------------
def test_format_validity_full() -> None:
    assert format_validity() == 1.0


def test_formats_differ_in_length() -> None:
    renders = all_renders()
    # the arXiv paper is the longest; the citation appendix the
    # shortest - formats genuinely differ
    assert len(renders["arxiv_paper_port"]) > len(
        renders["workshop_note_port"]
    )
    assert len(renders["citation_appendix_port"]) < len(
        renders["arxiv_paper_port"]
    )


def test_each_port_has_its_required_headers() -> None:
    for p in PORT_TYPES:
        text = render_port(p)
        for sec in schema_for(p).required_sections:
            if sec == "title":
                continue
            assert section_title(sec) in text


# --- limitation preservation --------------------
def test_limitation_preservation_full() -> None:
    assert limitation_preservation() == 1.0


def test_every_port_renders_limitations() -> None:
    for p in PORT_TYPES:
        assert section_title("limitations") in render_port(p)


# --- governance ---------------------------------
def test_no_forbidden_terms_across_ports() -> None:
    assert corpus_forbidden_hits() == ()
    for text in all_renders().values():
        assert forbidden_hits(text) == ()


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_renders_are_stable() -> None:
    assert all_renders() == all_renders()


def test_metrics_in_unit_interval() -> None:
    for m in (
        cross_port_claim_consistency(),
        cross_port_metric_consistency(), format_validity(),
        limitation_preservation(), replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_publishable() -> None:
    assert build_report().recommendation == VERDICT_PUBLISHABLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v25_3_multi_port.json")
    assert art["schema_version"] == "v25_3_multi_port_rendering"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v25_3_multi_port.json")
    disc = art["disclaimer"].lower()
    assert "byte-identical across ports" in disc
    assert "differ by format" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v25_3_multi_port.json")
    required = {
        "cross_port_claim_consistency",
        "cross_port_metric_consistency", "format_validity",
        "limitation_preservation", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v25_3_multi_port.json")
    live = build_multi_port_artifact()
    assert art == live


# --- deliverables -------------------------------
def test_citation_appendix_present_and_matches() -> None:
    doc = _read("citation_appendix.md")
    assert doc == render_citation_appendix()
    assert "arXiv:2501.14176" in doc
    assert forbidden_hits(doc) == ()


def test_reproducibility_statement_present_and_matches() -> None:
    doc = _read("reproducibility_statement.md")
    assert doc == render_reproducibility_statement()
    assert section_title("limitations") in doc
    assert forbidden_hits(doc) == ()
