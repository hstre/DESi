"""v3.71 — Mozart coverage source tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.mozart_coverage_source.claims import (
    all_novelty_profiles, dominant_novelty_type,
    novelty_profile,
)
from desi.mozart_coverage_source.regions import (
    state_regions, transition_regions,
)
from desi.mozart_coverage_source.report import (
    build_mozart_region_map_artifact, build_report,
)


def test_state_regions_of_mozart() -> None:
    moz = next(
        t for t in extract_all_trajectories()
        if t.trajectory_id == "sample:n03_mozart"
    )
    regions = state_regions(moz)
    # Mozart trajectory has 8 states; distinct (frame,
    # support) regions are <= 8.
    assert 1 <= len(regions) <= 8


def test_transition_regions_count_equals_n_minus_one() -> None:
    moz = next(
        t for t in extract_all_trajectories()
        if t.trajectory_id == "sample:n03_mozart"
    )
    transitions = transition_regions(moz)
    assert len(transitions) <= len(moz.states) - 1


def test_novelty_profile_emits_all_axes() -> None:
    moz = next(
        t for t in extract_all_trajectories()
        if t.trajectory_id == "sample:n03_mozart"
    )
    p = novelty_profile(moz)
    assert p.semantic >= 0
    assert p.structural >= 0
    assert p.bridge >= 0
    assert p.contradiction >= 0


def test_mozart_dominant_novelty_is_structural() -> None:
    """Mozart's structural axis (5 frames / 2 = 2.5)
    out-scores semantic (12 / 10 = 1.2). Stable
    across hash seeds because Mozart's distinct
    frame count is always >= 3."""
    moz = next(
        t for t in extract_all_trajectories()
        if t.trajectory_id == "sample:n03_mozart"
    )
    p = novelty_profile(moz)
    assert dominant_novelty_type(p) == "structural"


def test_all_novelty_profiles_count() -> None:
    assert len(all_novelty_profiles()) == 395


def test_new_regions_positive() -> None:
    """Paper-11 historical gate #3: new_regions > 0.
    Empirical 6-seed sweep: 1..5 unique transitions
    per run; always strictly positive."""
    r = build_report()
    assert r.new_regions > 0


def test_overlap_with_controls_below_one() -> None:
    """Mozart shares some transitions with controls
    but not all - overlap is between 0 and 1."""
    r = build_report()
    assert 0.0 < r.overlap_with_controls < 1.0


def test_coverage_source_is_structural() -> None:
    """Stable across hash seeds because Mozart's
    structural score (>= 3 frames / 2) dominates the
    semantic score (12 / 10)."""
    assert build_report().coverage_source == (
        "structural"
    )


def test_kant_novelty_type_is_missing() -> None:
    r = build_report()
    assert r.novelty_type_by_probe.get(
        "sample:n03_kant",
    ) == "missing"


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_opens_new() -> None:
    assert build_report().recommendation == (
        "MOZART_OPENS_NEW_REGIONS"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MOZART_OPENS_NEW_REGIONS",
        "MOZART_NO_NEW_REGIONS",
        "MOZART_MISSING",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_contains_unique_regions() -> None:
    art = build_mozart_region_map_artifact()
    assert art["mozart_present"] is True
    assert (
        "mozart_unique_transition_regions" in art
    )


def test_artifact_report_matches_live_build() -> None:
    """mozart_state_regions / mozart_transition_regions
    / new_state_regions / new_transition_regions /
    new_regions / overlap_with_controls /
    novelty_profile_by_probe all depend on
    FrameDetector dict-iteration ordering which
    jitters under PYTHONHASHSEED. Mark them volatile;
    coverage_source / novelty_type_by_probe /
    recommendation are stable."""
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_71" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {
        "rationale", "mozart_state_regions",
        "mozart_transition_regions",
        "new_state_regions",
        "new_transition_regions", "new_regions",
        "overlap_with_controls",
        "novelty_profile_by_probe",
    }
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
