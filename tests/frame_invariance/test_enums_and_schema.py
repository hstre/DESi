"""Tests for v3.5 enums + case schema (Aufgaben 5 + 8)."""
from __future__ import annotations

from desi.frame_invariance import (
    ALL_GROUPS,
    FrameInvarianceFailure,
    NEGATIVE_CONTROLS,
    ParaphraseGroup,
)
from desi.frames import FrameKind


_EXPECTED_FAILURES = {
    "none", "frame_drift", "frame_undeclared",
    "frame_conflict_unexpected", "forbidden_frame_hit",
    "pipeline_mismatch",
}


def test_failure_enum_has_exactly_six_values() -> None:
    assert len(list(FrameInvarianceFailure)) == 6


def test_failure_enum_set_matches_directive() -> None:
    assert {f.value for f in FrameInvarianceFailure} == _EXPECTED_FAILURES


def test_every_directive_failure_name_present() -> None:
    for name in (
        "NONE", "FRAME_DRIFT", "FRAME_UNDECLARED",
        "FRAME_CONFLICT_UNEXPECTED", "FORBIDDEN_FRAME_HIT",
        "PIPELINE_MISMATCH",
    ):
        assert hasattr(FrameInvarianceFailure, name)


def test_at_least_eighty_groups() -> None:
    assert len(ALL_GROUPS) >= 80


def test_per_frame_at_least_ten_groups() -> None:
    """Aufgabe 2 — every FrameKind (except FRAME_UNDECLARED) gets
    10 paraphrase groups."""
    from collections import Counter
    counts = Counter(g.expected_frame for g in ALL_GROUPS)
    for frame in FrameKind:
        if frame is FrameKind.FRAME_UNDECLARED:
            continue
        assert counts[frame] >= 10, (
            f"{frame.value}: only {counts[frame]} groups, need >= 10"
        )


def test_every_group_has_at_least_four_paraphrases() -> None:
    for g in ALL_GROUPS:
        assert len(g.paraphrases) >= 4, g.group_id


def test_every_group_carries_required_fields() -> None:
    for g in ALL_GROUPS:
        assert isinstance(g, ParaphraseGroup)
        for f in (
            "group_id", "expected_frame", "forbidden_frames",
            "expected_conflict_allowed", "canonical_text",
            "paraphrases",
        ):
            assert hasattr(g, f), f


def test_group_ids_unique() -> None:
    ids = [g.group_id for g in ALL_GROUPS]
    assert len(set(ids)) == len(ids)


def test_eight_negative_controls_exactly() -> None:
    assert len(NEGATIVE_CONTROLS) == 8


def test_negative_controls_have_distinct_frames() -> None:
    """Every NC pair specifies two different frames by design."""
    for nc in NEGATIVE_CONTROLS:
        assert nc.frame_a is not nc.frame_b, nc.nc_id
