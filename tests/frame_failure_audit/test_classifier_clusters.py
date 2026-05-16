"""Tests for v3.6 classifier + cluster + frame-breakdown
(Aufgaben 2, 3, 4)."""
from __future__ import annotations

from desi.frame_failure_audit import (
    FrameFailureClass,
    build_clusters,
    classify_all,
    extract_failures,
    per_frame_breakdown,
)


def test_classifier_returns_only_closed_enum_values() -> None:
    failures = extract_failures()
    closed = set(FrameFailureClass)
    assigned = classify_all(failures).values()
    for label in assigned:
        assert label in closed


def test_classifier_is_deterministic() -> None:
    failures = extract_failures()
    assert classify_all(failures) == classify_all(failures)


def test_clusters_have_min_size_two() -> None:
    """Aufgabe 3 — clusters must be >= 2 members."""
    summary = build_clusters(extract_failures())
    for c in summary.clusters:
        assert c.size >= 2


def test_singletons_have_size_one() -> None:
    summary = build_clusters(extract_failures())
    for c in summary.singletons:
        assert c.size == 1


def test_cluster_member_count_sums_to_30() -> None:
    summary = build_clusters(extract_failures())
    total = sum(c.size for c in summary.clusters)
    total += sum(c.size for c in summary.singletons)
    assert total == 30


def test_largest_cluster_size_consistent() -> None:
    summary = build_clusters(extract_failures())
    if summary.clusters:
        expected = max(c.size for c in summary.clusters)
        assert summary.largest_cluster_size == expected


def test_entropy_nonnegative() -> None:
    summary = build_clusters(extract_failures())
    assert summary.entropy_of_failure_distribution >= 0.0


def test_per_frame_breakdown_covers_all_failing_frames() -> None:
    """Aufgabe 4 — every frame that has at least one failure must
    appear in the breakdown."""
    failures = extract_failures()
    failing_frames = {f.expected_frame for f in failures}
    breakdown = per_frame_breakdown(failures)
    covered = {b.frame for b in breakdown}
    assert covered == failing_frames


def test_information_theoretic_has_a_dominant_class() -> None:
    """Aufgabe 4 — IF empirical_causal AND information_theoretic
    fail dominance, investigation fails. Here we verify info-theoretic
    has a dominant class."""
    from desi.frames import FrameKind
    breakdown = per_frame_breakdown(extract_failures())
    info = next(
        (b for b in breakdown if b.frame is FrameKind.INFORMATION_THEORETIC),
        None,
    )
    assert info is not None
    assert info.dominant_failure_class is not None


def test_empirical_causal_has_a_dominant_class() -> None:
    from desi.frames import FrameKind
    breakdown = per_frame_breakdown(extract_failures())
    causal = next(
        (b for b in breakdown if b.frame is FrameKind.EMPIRICAL_CAUSAL),
        None,
    )
    assert causal is not None
    assert causal.dominant_failure_class is not None


def test_cluster_summary_deterministic_across_runs() -> None:
    a = build_clusters(extract_failures())
    b = build_clusters(extract_failures())
    assert a.to_dict() == b.to_dict()
