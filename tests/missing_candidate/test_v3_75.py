"""v3.75 — candidate reconstruction tests."""
from __future__ import annotations

import json
import pathlib

from desi.missing_candidate.candidate import (
    PRE_AUDIT_INDEX, reconstruct_candidate,
)
from desi.missing_candidate.reconstruct import (
    all_candidate_matches,
)
from desi.missing_candidate.report import (
    NEPTUN_MATCH_FLOOR,
    build_missing_candidate_reconstruction_artifact,
    build_report,
)
from desi.missing_localization.localize import (
    all_localizations,
)


def test_pre_audit_index_is_two() -> None:
    assert PRE_AUDIT_INDEX == 2


def test_match_floor_anchor() -> None:
    assert NEPTUN_MATCH_FLOOR == 0.70


def test_only_one_candidate_reconstructed() -> None:
    """Only the BRIDGE localization yields a non-
    empty orphan set; the other three removals are
    skipped from reconstruction."""
    matches = all_candidate_matches()
    assert len(matches) == 1


def test_bridge_candidate_role_is_bridge() -> None:
    m = all_candidate_matches()[0]
    assert m.role == "bridge"
    assert m.removed_id == "v23:R5_02"


def test_bridge_candidate_orphan_count_is_twelve() -> None:
    m = all_candidate_matches()[0]
    assert m.candidate["orphan_count"] == 12
    assert m.actual["coverage"] == 12


def test_frame_match() -> None:
    """Expected frame (5.0 - mode of orphan
    frame_id@2) matches the bridge anchor's
    frame_id@2 (also 5.0)."""
    m = all_candidate_matches()[0]
    assert m.frame_match is True


def test_support_match() -> None:
    """Both orphans and bridge anchor have
    support_state = 0.0 at index 2."""
    m = all_candidate_matches()[0]
    assert m.support_match is True


def test_bridge_match_is_true() -> None:
    m = all_candidate_matches()[0]
    assert m.bridge_match is True


def test_coverage_match_is_true() -> None:
    m = all_candidate_matches()[0]
    assert m.coverage_match is True


def test_novelty_in_predicted_range() -> None:
    """Actual novelty (5.0) falls within the
    predicted range [5.0, 5.0]."""
    m = all_candidate_matches()[0]
    assert m.novelty_match is True


def test_candidate_match_score_meets_gate() -> None:
    """Neptun concept gate #3:
    candidate_match_score >= 0.70."""
    r = build_report()
    assert r.candidate_match_score >= (
        NEPTUN_MATCH_FLOOR
    )


def test_candidate_match_score_is_perfect() -> None:
    """Empirical: all 5 features match -> score
    1.0."""
    assert build_report().candidate_match_score == 1.0


def test_expected_region_overlap_is_one() -> None:
    assert build_report().expected_region_overlap == 1.0


def test_role_reconstruction_accuracy_is_one() -> None:
    assert build_report().role_reconstruction_accuracy == 1.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_usable() -> None:
    assert build_report().recommendation == (
        "CANDIDATE_RECONSTRUCTION_USABLE"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CANDIDATE_RECONSTRUCTION_USABLE",
        "CANDIDATE_RECONSTRUCTION_WEAK",
        "CANDIDATE_RECONSTRUCTION_FAILED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_matches() -> None:
    art = build_missing_candidate_reconstruction_artifact()
    assert len(art["matches"]) == 1


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_75" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
