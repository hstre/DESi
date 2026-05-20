"""v3.79 — redundancy class census tests."""
from __future__ import annotations

import json
import pathlib

from desi.redundancy_masking.equivalence import (
    PROBE_RADIUS, exact_duplicate_count,
    largest_redundancy_class,
    partial_overlap_count, partial_overlaps,
    redundancy_classes,
)
from desi.redundancy_masking.report import (
    build_redundancy_class_census_artifact,
    build_report,
)


def test_probe_radius_matches_v350() -> None:
    assert PROBE_RADIUS == 3.5


def test_three_redundancy_classes() -> None:
    """Empirical: 121-cov, 12-cov, 0-cov classes."""
    classes = redundancy_classes()
    assert len(classes) == 3


def test_class_sizes() -> None:
    """Sorted by member count descending then
    coverage size descending. Empirical sizes:
    8 (121), 8 (12), 4 (0)."""
    classes = redundancy_classes()
    sizes = [len(c.members) for c in classes]
    assert sizes == [8, 8, 4]


def test_class_coverage_sizes() -> None:
    classes = redundancy_classes()
    cov_sizes = sorted(
        c.coverage_size for c in classes
    )
    assert cov_sizes == [0, 12, 121]


def test_high_coverage_class_membership() -> None:
    """The directive's v23:R5_04 and v314:D02 sit in
    the 121-coverage class."""
    classes = redundancy_classes()
    by_size = {
        c.coverage_size: set(c.members)
        for c in classes
    }
    assert "v23:R5_04" in by_size[121]
    assert "v314:D02" in by_size[121]


def test_bridge_anchor_in_twelve_class() -> None:
    classes = redundancy_classes()
    by_size = {
        c.coverage_size: set(c.members)
        for c in classes
    }
    assert "v23:R5_02" in by_size[12]


def test_low_anchor_in_zero_class() -> None:
    classes = redundancy_classes()
    by_size = {
        c.coverage_size: set(c.members)
        for c in classes
    }
    assert "v23:R4_04" in by_size[0]


def test_exact_duplicate_count_is_three() -> None:
    """All three classes have >= 2 members."""
    assert exact_duplicate_count(
        redundancy_classes(),
    ) == 3


def test_largest_redundancy_class_is_eight() -> None:
    assert largest_redundancy_class(
        redundancy_classes(),
    ) == 8


def test_no_partial_overlaps() -> None:
    """All three classes have disjoint coverage in
    this corpus."""
    overlaps = partial_overlaps(redundancy_classes())
    for o in overlaps:
        assert o.overlap_size == 0
        assert o.overlap_fraction == 0.0
    assert partial_overlap_count(overlaps) == 0


def test_report_counts() -> None:
    r = build_report()
    assert r.redundancy_class_count == 3
    assert r.exact_duplicate_count == 3
    assert r.partial_overlap_count == 0
    assert r.largest_redundancy_class == 8


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_classes_found() -> None:
    assert build_report().recommendation == (
        "REDUNDANCY_CLASSES_FOUND"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "REDUNDANCY_CLASSES_FOUND",
        "NO_REDUNDANCY", "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_summary_present() -> None:
    art = build_redundancy_class_census_artifact()
    assert "summary" in art
    assert art["summary"][
        "redundancy_class_count"
    ] == 3


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_79" / "report.json").read_text(
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
