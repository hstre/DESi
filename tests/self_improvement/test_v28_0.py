"""v28.0 - Improvement Candidate Harvester tests."""
from __future__ import annotations

import json
import pathlib

from desi.self_improvement import (
    ALLOWED_TARGETS, FORBIDDEN_TARGETS, HUMAN_APPROVAL_REQUIRED,
    IMPROVEMENT_CLASSES, ImprovementClass, authority_marker_hits,
    build_candidates_artifact, build_report,
    candidate_extraction_consistency, candidates,
    candidates_targeting_forbidden, classify_target,
    epistemic_neutrality, is_forbidden_target, is_safe_target,
    is_valid_source, provenance_integrity, replay_stability,
    safe_candidates, unsafe_candidates, unsafe_detection,
)
from desi.self_improvement.report import (
    REPORT_VERDICTS, VERDICT_SCREENED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "self_improvement"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- closed taxonomy & constraints --------------
def test_improvement_classes_closed() -> None:
    assert IMPROVEMENT_CLASSES == tuple(
        c.value for c in ImprovementClass
    )
    assert "UNSAFE" in IMPROVEMENT_CLASSES


def test_forbidden_targets_classify_unsafe() -> None:
    for area in FORBIDDEN_TARGETS:
        assert is_forbidden_target(area)
        assert not is_safe_target(area)
        assert classify_target(area) == "UNSAFE"


def test_allowed_targets_are_safe() -> None:
    for area in ALLOWED_TARGETS:
        assert is_safe_target(area)
        assert classify_target(area) != "UNSAFE"


def test_human_approval_required_constant() -> None:
    assert HUMAN_APPROVAL_REQUIRED is True


# --- candidate extraction -----------------------
def test_candidate_extraction_consistency_full() -> None:
    assert candidate_extraction_consistency() == 1.0


def test_every_candidate_well_formed() -> None:
    for c in candidates():
        assert c.is_well_formed()


def test_safe_and_unsafe_split() -> None:
    assert len(safe_candidates()) >= 1
    assert len(unsafe_candidates()) >= 1
    assert (
        len(safe_candidates()) + len(unsafe_candidates())
        == len(candidates())
    )


# --- unsafe detection (core safety) -------------
def test_unsafe_detection_full() -> None:
    assert unsafe_detection() == 1.0


def test_forbidden_core_candidates_flagged_unsafe() -> None:
    flagged = set(candidates_targeting_forbidden())
    assert flagged  # there are some, deliberately
    for c in candidates():
        if is_forbidden_target(c.target_area):
            assert c.candidate_id in flagged
            assert c.is_safe is False
            assert c.improvement_class == "UNSAFE"


def test_no_safe_candidate_targets_forbidden() -> None:
    for c in safe_candidates():
        assert not is_forbidden_target(c.target_area)


# --- provenance ---------------------------------
def test_provenance_integrity_full() -> None:
    assert provenance_integrity() == 1.0


def test_every_candidate_sourced_from_corpus() -> None:
    for c in candidates():
        assert is_valid_source(c.source_claim_id)
        assert c.source_paper_id


# --- epistemic neutrality -----------------------
def test_epistemic_neutrality_full() -> None:
    assert epistemic_neutrality() == 1.0
    assert authority_marker_hits() == ()


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        candidate_extraction_consistency(), unsafe_detection(),
        provenance_integrity(), epistemic_neutrality(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_screened() -> None:
    assert build_report().recommendation == VERDICT_SCREENED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v28_0_candidates.json")
    assert art["schema_version"] == (
        "v28_0_improvement_candidates"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v28_0_candidates.json")
    disc = art["disclaimer"].lower()
    assert "nothing is applied" in disc
    assert "human approval is mandatory" in disc
    assert "unsafe and contained" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v28_0_candidates.json")
    required = {
        "candidate_extraction_consistency", "unsafe_detection",
        "provenance_integrity", "epistemic_neutrality",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_records_human_approval() -> None:
    art = _load("v28_0_candidates.json")
    assert art["human_approval_required"] is True


def test_artifact_full_matches_live_build() -> None:
    art = _load("v28_0_candidates.json")
    live = build_candidates_artifact()
    assert art == live
