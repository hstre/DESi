"""v23.0 - Direct Paper Anchoring tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.icrl_followup_revision import (
    addressed_problem_ids, addresses_section_4_6,
    build_anchoring_artifact, build_report, claims,
    exploration_gap_mapping, generic_claim_reduction,
    paper_alignment, problems, related_work_section,
    section_forbidden_hits, section_grounding,
    unaddressed_problem_ids, unconnected_claims,
)
from desi.icrl_followup_revision.report import (
    REPORT_VERDICTS, VERDICT_ANCHORED,
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
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- every claim anchored to the base paper -----
def test_paper_alignment_full() -> None:
    assert paper_alignment() >= 0.90
    assert unconnected_claims() == ()


def test_all_open_problems_addressed() -> None:
    assert exploration_gap_mapping() >= 0.90
    assert unaddressed_problem_ids() == ()
    assert set(addressed_problem_ids()) == {
        p.problem_id for p in problems()
    }


def test_section_grounding_full() -> None:
    assert section_grounding() >= 0.90
    for c in claims():
        assert c.sprint_source


def test_generic_reduced() -> None:
    assert generic_claim_reduction() >= 0.90


# --- the mandatory anchors ----------------------
def test_addresses_section_4_6() -> None:
    assert addresses_section_4_6() is True
    sec = related_work_section()
    assert "Section 4.6" in sec
    assert "complementary" in sec.lower()


def test_base_problems_cover_required_topics() -> None:
    texts = " ".join(p.text.lower() for p in problems())
    assert "collapse" in texts          # exploration collapse
    assert "sparse" in texts            # sparse reward failure
    assert "repetitive" in texts        # repetitive trajectory


def test_no_forbidden_terms_in_section() -> None:
    assert section_forbidden_hits() == ()
    assert forbidden_hits(related_work_section()) == ()


def test_metrics_in_unit_interval() -> None:
    for m in (
        paper_alignment(), exploration_gap_mapping(),
        section_grounding(), generic_claim_reduction(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation in set(REPORT_VERDICTS)
    )


def test_recommendation_is_anchored() -> None:
    assert build_report().recommendation == VERDICT_ANCHORED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v23_0_anchoring.json")
    assert art["schema_version"] == (
        "v23_0_direct_paper_anchoring"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v23_0_anchoring.json")
    disc = art["disclaimer"].lower()
    assert "complementary" in disc
    assert "not a replacement" in disc
    assert "section 4.6" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v23_0_anchoring.json")
    required = {
        "paper_alignment", "exploration_gap_mapping",
        "section_grounding", "generic_claim_reduction",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v23_0_anchoring.json")
    live = build_anchoring_artifact()
    assert art == live
