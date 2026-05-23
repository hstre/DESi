"""v25.0 - Output Port Schema tests."""
from __future__ import annotations

import json
import pathlib

from desi.output_ports import (
    BASE_PAPER_REF, PORT_TYPES, PROVENANCE_KINDS, SECTION_TYPES,
    PortType, SectionType, build_report, build_schema_artifact,
    citation_requirement_visibility,
    limitation_requirement_visibility, port_schema_coverage,
    port_schemas, replay_stability, required_section_visibility,
    required_sections, schema_for, section_title,
)
from desi.output_ports.report import (
    REPORT_VERDICTS, VERDICT_FORMAL,
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


# --- closed sets --------------------------------
def test_port_types_closed() -> None:
    assert PORT_TYPES == tuple(p.value for p in PortType)
    assert len(PORT_TYPES) == 5


def test_section_types_closed() -> None:
    assert SECTION_TYPES == tuple(s.value for s in SectionType)


def test_provenance_kinds() -> None:
    assert PROVENANCE_KINDS == (
        "claim_lineage", "artifact_link", "metric_derivation",
        "reference", "limitation_link", "replay_hash",
    )


# --- every port formally defined ----------------
def test_port_schema_coverage_full() -> None:
    assert port_schema_coverage() == 1.0


def test_every_port_complete() -> None:
    for s in port_schemas():
        assert s.is_complete()
        assert s.required_sections
        assert s.forbidden_patterns
        assert s.provenance.allowed_kinds == PROVENANCE_KINDS


def test_required_sections_are_known() -> None:
    for s in port_schemas():
        for sec in s.required_sections:
            assert sec in SECTION_TYPES
            assert section_title(sec)


# --- arxiv port has the 13 mandated sections ----
def test_arxiv_required_sections() -> None:
    req = required_sections(PortType.ARXIV_PAPER.value)
    expected = (
        SectionType.TITLE.value, SectionType.ABSTRACT.value,
        SectionType.INTRODUCTION.value,
        SectionType.RELATED_WORK.value,
        SectionType.PROBLEM_STATEMENT.value,
        SectionType.METHOD.value,
        SectionType.EXPERIMENTAL_CONDITIONS.value,
        SectionType.METRICS.value, SectionType.RESULTS.value,
        SectionType.LIMITATIONS.value,
        SectionType.REPRODUCIBILITY_STATEMENT.value,
        SectionType.CONCLUSION.value,
        SectionType.REFERENCES.value,
    )
    assert req == expected
    assert len(req) == 13


# --- section visibility -------------------------
def test_required_section_visibility_full() -> None:
    assert required_section_visibility() == 1.0


# --- citation rules are per-port ----------------
def test_citation_requirement_visibility_full() -> None:
    assert citation_requirement_visibility() == 1.0


def test_paper_ports_must_cite_base_paper() -> None:
    for p in (
        PortType.ARXIV_PAPER.value,
        PortType.WORKSHOP_NOTE.value,
        PortType.TECHNICAL_REPORT.value,
    ):
        s = schema_for(p)
        assert s.citation.required
        assert BASE_PAPER_REF in s.citation.must_cite


def test_citation_rules_are_port_dependent() -> None:
    mins = {
        s.port_type: s.citation.min_citations
        for s in port_schemas()
    }
    # the reproducibility statement does not require a citation
    assert mins[PortType.REPRODUCIBILITY_STATEMENT.value] == 0
    assert mins[PortType.ARXIV_PAPER.value] >= 1


# --- limitations mandatory ----------------------
def test_limitation_requirement_visibility_full() -> None:
    assert limitation_requirement_visibility() == 1.0


def test_every_port_mandates_limitations() -> None:
    for s in port_schemas():
        assert s.limitation.required
        assert s.limitation.must_be_sandbox_scoped


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        port_schema_coverage(), required_section_visibility(),
        citation_requirement_visibility(),
        limitation_requirement_visibility(), replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_formalised() -> None:
    assert build_report().recommendation == VERDICT_FORMAL


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v25_0_schema.json")
    assert art["schema_version"] == "v25_0_output_port_schema"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v25_0_schema.json")
    disc = art["disclaimer"].lower()
    assert "deterministic interface" in disc
    assert "not free text generation" in disc
    assert "no central claim may be naked" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v25_0_schema.json")
    required = {
        "port_schema_coverage", "required_section_visibility",
        "citation_requirement_visibility",
        "limitation_requirement_visibility", "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v25_0_schema.json")
    live = build_schema_artifact()
    assert art == live
