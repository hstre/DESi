"""v3.69 — Mozart probe coverage tests."""
from __future__ import annotations

import json
import pathlib

from desi.mozart_probe.coverage import (
    HISTORICAL_PROBES, all_coverages,
    coverage_percentile, historical_coverages,
    probe_coverage,
)
from desi.mozart_probe.reconstruct import (
    historical_timelines, missing_probes,
    present_probes, probe_timeline,
)
from desi.mozart_probe.report import (
    MOZART_PERCENTILE_FLOOR,
    build_mozart_coverage_artifact, build_report,
)


def test_historical_probes_match_directive() -> None:
    assert HISTORICAL_PROBES == (
        "sample:n03_mozart",
        "sample:n03_darwin",
        "sample:n03_kant",
    )


def test_kant_is_documented_missing() -> None:
    """sample:n03_kant is absent from the corpus."""
    assert "sample:n03_kant" in missing_probes()
    assert "sample:n03_kant" not in present_probes()


def test_mozart_and_darwin_present() -> None:
    assert "sample:n03_mozart" in present_probes()
    assert "sample:n03_darwin" in present_probes()


def test_missing_probe_marked_unavailable() -> None:
    kant = probe_coverage("sample:n03_kant")
    assert kant.available is False
    assert kant.coverage_score == 0.0


def test_mozart_coverage_score_higher_than_darwin() -> None:
    moz = probe_coverage("sample:n03_mozart")
    dar = probe_coverage("sample:n03_darwin")
    assert moz.coverage_score > dar.coverage_score


def test_mozart_coverage_percentile_meets_gate() -> None:
    """Paper-11 historical gate #1: mozart
    coverage_percentile >= 0.90."""
    r = build_report()
    assert r.mozart_coverage_percentile >= (
        MOZART_PERCENTILE_FLOOR
    )


def test_mozart_coverage_percentile_is_max() -> None:
    """Empirical: mozart is the strict maximum across
    the corpus."""
    assert build_report().mozart_coverage_percentile == 1.0


def test_mozart_gap_events_is_two() -> None:
    """Mozart enters GAP_DETECTED for two consecutive
    states (MID_RUN_GAP pattern)."""
    assert probe_coverage(
        "sample:n03_mozart",
    ).gap_events == 2


def test_darwin_gap_events_is_one() -> None:
    """Darwin's GAP is at the terminal state only."""
    assert probe_coverage(
        "sample:n03_darwin",
    ).gap_events == 1


def test_mozart_distinct_frames_above_typical() -> None:
    """Mozart visits several distinct frame_id
    values; the exact count jitters across
    PYTHONHASHSEED because v3.32 FrameDetector
    iterates a dict, but the count is always >= 3
    (well above the median trajectory's 2)."""
    assert probe_coverage(
        "sample:n03_mozart",
    ).distinct_frames >= 3


def test_mozart_trajectory_length_is_eight() -> None:
    assert probe_coverage(
        "sample:n03_mozart",
    ).trajectory_length == 8


def test_probe_timeline_for_kant_unavailable() -> None:
    t = probe_timeline("sample:n03_kant")
    assert t.available is False
    assert t.support_path == ()


def test_probe_timeline_for_mozart_complete() -> None:
    t = probe_timeline("sample:n03_mozart")
    assert t.available is True
    assert len(t.support_path) == 8
    assert t.gap_indices == (6, 7)


def test_historical_coverages_count() -> None:
    assert len(historical_coverages()) == 3


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_coverage_percentile_helper_basic() -> None:
    moz = probe_coverage("sample:n03_mozart")
    pct = coverage_percentile(moz, all_coverages())
    assert pct >= MOZART_PERCENTILE_FLOOR


def test_recommendation_is_outlier() -> None:
    assert build_report().recommendation == (
        "MOZART_IS_COVERAGE_OUTLIER"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MOZART_IS_COVERAGE_OUTLIER",
        "MOZART_NOT_OUTLIER",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_contains_timelines() -> None:
    art = build_mozart_coverage_artifact()
    assert len(art["coverages"]) == 3
    assert len(art["timelines"]) == 3


def test_artifact_report_matches_live_build() -> None:
    """coverage_by_probe and coverage_percentile_by_
    probe depend on distinct_frames counts, which
    jitter under PYTHONHASHSEED via the v3.32
    FrameDetector. Mark those plus the timelines
    (which include hash-sensitive frame_path) as
    volatile alongside rationale; the stable
    headline (present/missing probes,
    bridge_by_probe, gap_events_by_probe,
    recommendation) is compared exactly."""
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_69" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {
        "rationale", "coverage_by_probe",
        "coverage_percentile_by_probe",
        "mozart_coverage_percentile",
        "timelines",
    }
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
