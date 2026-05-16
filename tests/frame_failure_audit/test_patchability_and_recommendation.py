"""Tests for v3.6 patchability + contamination + recommendation
(Aufgaben 5, 6, 7, 9)."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.frame_failure_audit import (
    NEGATIVE_CONTROLS,
    assess_patchability,
    build_audit_report,
    build_clusters,
    extract_failures,
    probe_contamination,
)


def test_ten_negative_controls() -> None:
    assert len(NEGATIVE_CONTROLS) == 10


def test_negative_controls_have_distinct_decoy_pairs() -> None:
    for nc in NEGATIVE_CONTROLS:
        assert nc.expected_frame is not nc.decoy_for_frame


def test_probe_contamination_returns_unit_interval() -> None:
    failures = extract_failures()
    summary = build_clusters(failures)
    for c in summary.clusters:
        p = probe_contamination(c, failures)
        assert 0.0 <= p.contamination_risk <= 1.0


def test_safe_patch_requires_zero_contamination() -> None:
    failures = extract_failures()
    summary = build_clusters(failures)
    for c in summary.clusters:
        v = assess_patchability(c, failures)
        if v.safe_patch_candidate:
            assert v.contamination.contamination_risk == 0.0


def test_safe_patch_requires_minimum_size_three() -> None:
    failures = extract_failures()
    summary = build_clusters(failures)
    for c in summary.clusters:
        v = assess_patchability(c, failures)
        if v.safe_patch_candidate:
            assert c.size >= 3


def test_negative_control_precision_is_one() -> None:
    """Aufgabe 7 — precision = 1.0 means the detector does not
    collapse any decoy paraphrase into its decoy frame."""
    rep = build_audit_report(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    assert rep.negative_control_precision == 1.0


def test_recommended_next_is_NONE_when_no_cluster_is_safe() -> None:
    """The v3.6 audit's correct conservative verdict: zero safe
    patch candidates → recommended_next = 'NONE'."""
    rep = build_audit_report(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    safe_count = sum(
        1 for v in rep.patchability if v.safe_patch_candidate
    )
    if safe_count == 0:
        assert rep.recommended_next == "NONE"
    else:
        # If a future change makes a cluster safe, the recommendation
        # must be that cluster's id (deterministic by sort).
        assert rep.recommended_next != "NONE"


def test_report_has_replay_hash_sixteen_hex() -> None:
    rep = build_audit_report(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    assert len(rep.replay_hash) == 16
    int(rep.replay_hash, 16)


def test_two_runs_produce_identical_replay_hash() -> None:
    now = datetime.now(timezone.utc)
    a = build_audit_report(started_at=now, finished_at=now)
    b = build_audit_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_report_to_dict_shape() -> None:
    rep = build_audit_report(
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    d = rep.to_dict()
    for k in (
        "total_failures", "failures", "cluster_summary",
        "per_frame_breakdown", "patchability",
        "negative_control_outcomes", "negative_control_precision",
        "recommended_next", "replay_hash",
    ):
        assert k in d
