"""v26 - Rentschler Follow-Up Paper (arXiv output port) tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import FORBIDDEN_TERMS, forbidden_hits
import re
from desi.rentschler_followup import (
    CORE_THESIS, GATE_PASS_STATEMENT, MECHANISM_MARKERS,
    SECTION_ORDER, base_paper_in_paper, build_followup_artifact,
    build_report, build_section, citation_integrity,
    desi_mechanism_clarity, gate_conditions,
    gate_failing_conditions, gate_passes_all, no_naked_claims,
    paper_alignment, paper_forbidden_hits, render,
    replay_stability, required_sections, result_traceability,
    section_completeness, section_title,
)
from desi.rentschler_followup.report import (
    REPORT_VERDICTS, VERDICT_SHIPPABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "icrl_followup"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- mandated sections --------------------------
def test_fourteen_mandated_sections() -> None:
    assert SECTION_ORDER == (
        "title", "abstract", "introduction", "related_work",
        "problem_statement", "desi_governance_layer",
        "experimental_conditions", "metrics", "results",
        "discussion", "limitations",
        "reproducibility_statement", "conclusion", "references",
    )
    assert len(required_sections()) == 14


def test_section_completeness_full() -> None:
    assert section_completeness() == 1.0


def test_all_section_headers_present() -> None:
    paper = render()
    for key in SECTION_ORDER:
        if key == "title":
            continue
        assert section_title(key) in paper
    assert "The DESi Governance Layer" in paper
    assert "Discussion" in paper


# --- direct anchoring to Section 4.6 ------------
def test_paper_alignment_full() -> None:
    assert paper_alignment() >= 0.95


def test_paper_anchors_section_4_6() -> None:
    assert "Section 4.6" in render()


# --- DESi mechanism clarity (no mythology) ------
def test_desi_mechanism_clarity_full() -> None:
    assert desi_mechanism_clarity() >= 0.95


def test_desi_section_states_what_desi_is() -> None:
    section = build_section("desi_governance_layer").lower()
    for marker in MECHANISM_MARKERS:
        assert marker in section


def test_no_desi_mythology() -> None:
    # the hard forbidden terms (AGI, Superintelligence, Kant,
    # Popper, World model, ...) must not appear anywhere
    paper = render()
    assert forbidden_hits(paper) == ()
    low = paper.lower()
    for term in FORBIDDEN_TERMS:
        t = term.lower()
        if " " in t or "-" in t:
            assert t not in low
        else:
            assert not re.search(rf"\b{re.escape(t)}\b", low)


# --- citation integrity -------------------------
def test_citation_integrity_full() -> None:
    assert citation_integrity() >= 0.95


def test_base_paper_cited() -> None:
    assert base_paper_in_paper() is True
    paper = render()
    assert "arXiv:2501.14176" in paper
    assert "Rentschler and Roberts" in paper


# --- result traceability / no naked claims ------
def test_result_traceability_full() -> None:
    assert result_traceability() >= 0.95


def test_no_naked_claims_full() -> None:
    assert no_naked_claims() >= 0.95


def test_every_number_has_derivation() -> None:
    # every result line names the sprint it was derived in
    paper = render()
    from desi.icrl_followup_conditions import results
    for r in results():
        assert str(round(r.value, 6)) in paper
        assert r.sprint_source in paper


# --- core thesis present ------------------------
def test_core_thesis_present_and_hedged() -> None:
    paper = render()
    assert CORE_THESIS in paper
    # the thesis is hedged, not asserted as demonstrated
    assert "may increase" in CORE_THESIS
    assert "not a demonstrated property" in paper


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_thresholds() -> None:
    by = {c.name: c for c in gate_conditions()}
    assert by["paper_alignment"].value >= 0.95
    assert by["desi_mechanism_clarity"].value >= 0.95
    assert by["citation_integrity"].value >= 0.95
    assert by["result_traceability"].value >= 0.95
    assert by["no_naked_claims"].value >= 0.95
    assert by["replay_stability"].value == 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_shippable() -> None:
    assert build_report().recommendation == VERDICT_SHIPPABLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_no_forbidden_hits() -> None:
    assert paper_forbidden_hits() == ()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v26_rentschler_followup.json")
    assert art["schema_version"] == (
        "v26_rentschler_followup_arxiv_port"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v26_rentschler_followup.json")
    disc = art["disclaimer"].lower()
    assert "section 4.6" in disc
    assert "no mythology" in disc
    assert "provenance-bound export" in disc


def test_artifact_gate_passes() -> None:
    art = _load("v26_rentschler_followup.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == "SHIPPABLE_TO_RENTSCHLER"
    assert art["gate_statement"] == GATE_PASS_STATEMENT


def test_artifact_full_matches_live_build() -> None:
    art = _load("v26_rentschler_followup.json")
    live = build_followup_artifact()
    assert art == live


# --- deliverable paper --------------------------
def test_rendered_paper_present_and_matches() -> None:
    paper = _read("rentschler_followup_arxiv_port.md")
    assert paper == render()
    assert CORE_THESIS in paper
    assert forbidden_hits(paper) == ()
