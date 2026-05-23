"""v22.0 - Scientific Hypothesis Exploration tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import (
    FORBIDDEN_TERMS, anchored_fraction, build_hypotheses_artifact,
    build_report, forbidden_hits, forbidden_in_candidates,
    hypotheses, overreach_detection, overreach_hypotheses,
    paper_candidate_quality, paper_candidates, speculative_drift,
    technical_grounding,
)
from desi.scientific_rendering.report import (
    REPORT_VERDICTS, VERDICT_SEPARATED,
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


# --- forbidden-term detection -------------------
def test_forbidden_terms_defined() -> None:
    assert "AGI" in FORBIDDEN_TERMS
    assert "Breakthrough" in FORBIDDEN_TERMS
    assert "World model" in FORBIDDEN_TERMS


def test_forbidden_detector_word_boundary() -> None:
    """'agi' must not trigger inside ordinary words."""
    assert forbidden_hits("the magic of imagination") == ()
    assert "AGI" in forbidden_hits("a step toward AGI systems")


def test_no_forbidden_in_candidates() -> None:
    assert forbidden_in_candidates() is False
    for h in paper_candidates():
        assert forbidden_hits(h.text) == ()


# --- triage: grounded vs hype -------------------
def test_paper_candidates_grounded() -> None:
    assert len(paper_candidates()) >= 1
    assert paper_candidate_quality() >= 0.90
    assert technical_grounding() >= 0.90
    assert anchored_fraction() >= 0.90


def test_overreach_detected() -> None:
    assert overreach_detection() == 1.0
    assert len(overreach_hypotheses()) >= 1


def test_speculation_present_in_wild() -> None:
    """The Wild Explorer genuinely speculates - the test is
    detection, not absence."""
    assert speculative_drift() > 0.0


def test_hype_hypotheses_rejected() -> None:
    """Hypotheses with forbidden terms must not be paper
    candidates."""
    cand_ids = {h.hyp_id for h in paper_candidates()}
    for h in hypotheses():
        if forbidden_hits(h.text):
            assert h.hyp_id not in cand_ids


def test_metrics_in_unit_interval() -> None:
    for m in (
        paper_candidate_quality(), speculative_drift(),
        technical_grounding(), overreach_detection(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_triaged() -> None:
    assert build_report().recommendation == VERDICT_SEPARATED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v22_0_hypotheses.json")
    assert art["schema_version"] == (
        "v22_0_scientific_hypothesis_exploration"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v22_0_hypotheses.json")
    disc = art["disclaimer"].lower()
    assert "no global intelligence claim" in disc
    assert "replaces no rl" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v22_0_hypotheses.json")
    required = {
        "paper_candidate_quality",
        "speculative_drift",
        "technical_grounding",
        "overreach_detection",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v22_0_hypotheses.json")
    live = build_hypotheses_artifact()
    assert art == live
