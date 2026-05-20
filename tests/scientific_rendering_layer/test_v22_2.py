"""v22.2 - Scientific Rendering Layer tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import FORBIDDEN_TERMS, forbidden_hits
from desi.scientific_rendering_layer import (
    SECTION_ORDER, abstract_is_conservative,
    all_sections_present, build_rendering_artifact,
    build_report, claim_conservatism, document_forbidden_hits,
    full_document, hype_free, sandbox_honesty,
    scientific_style_integrity, uncertainty_visibility,
)
from desi.scientific_rendering_layer.report import (
    REPORT_VERDICTS, VERDICT_RENDERED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "scientific_rendering"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def _paper() -> str:
    return (
        _ARTIFACT_ROOT / "draft_exploration_governance_paper.md"
    ).read_text(encoding="utf-8")


# --- paper structure ----------------------------
def test_all_sections_present() -> None:
    assert all_sections_present() is True
    assert len(SECTION_ORDER) == 6
    for s in (
        "Abstract", "Motivation", "Experimental Setup",
        "Results", "Limitations", "Conclusion",
    ):
        assert s in SECTION_ORDER


# --- no hype, no forbidden terms ----------------
def test_no_forbidden_terms_in_document() -> None:
    assert document_forbidden_hits() == ()
    assert forbidden_hits(full_document()) == ()


def test_style_is_sober() -> None:
    assert scientific_style_integrity() >= 0.90
    assert hype_free() is True


def test_claims_conservative() -> None:
    assert claim_conservatism() >= 0.90
    assert abstract_is_conservative() is True


def test_uncertainty_and_honesty() -> None:
    assert uncertainty_visibility() >= 0.90
    assert sandbox_honesty() is True


def test_metrics_in_unit_interval() -> None:
    for m in (
        scientific_style_integrity(), claim_conservatism(),
        uncertainty_visibility(),
    ):
        assert 0.0 <= m <= 1.0


# --- the draft paper deliverable ----------------
def test_draft_paper_present_and_clean() -> None:
    paper = _paper()
    assert paper.startswith("# ")
    assert "## Abstract" in paper
    assert "## Limitations" in paper
    # the hard rule: no forbidden term anywhere in the paper
    assert forbidden_hits(paper) == ()


def test_draft_paper_matches_render() -> None:
    assert _paper() == full_document()


def test_draft_paper_scoped_to_sandbox() -> None:
    low = _paper().lower()
    assert "synthetic" in low
    assert "beyond the sandbox" in low
    assert "we make no claim" in low or "no claim" in low


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_rendered() -> None:
    assert build_report().recommendation == VERDICT_RENDERED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v22_2_rendering.json")
    assert art["schema_version"] == (
        "v22_2_scientific_rendering_layer"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v22_2_rendering.json")
    required = {
        "scientific_style_integrity",
        "claim_conservatism",
        "uncertainty_visibility",
        "sandbox_honesty",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v22_2_rendering.json")
    live = build_rendering_artifact()
    assert art == live
