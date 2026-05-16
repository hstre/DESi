"""Tests for FrameInvarianceRunner (Aufgaben 3 + 8)."""
from __future__ import annotations

from desi.frame_invariance import (
    FrameInvarianceFailure,
    FrameInvarianceRunner,
)
from desi.frames import FrameKind


def test_runner_emits_at_least_four_hundred_results() -> None:
    """80 groups × (1 canonical + 4 paraphrases) = 400 minimum."""
    run = FrameInvarianceRunner().run()
    assert len(run.results) >= 400


def test_runner_negative_controls_emitted() -> None:
    run = FrameInvarianceRunner().run()
    assert len(run.negative_controls) == 8


def test_results_carry_required_fields() -> None:
    run = FrameInvarianceRunner().run()
    r = run.results[0]
    for f in (
        "case_id", "group_id", "text",
        "expected_frame", "detected_frame",
        "state", "compatible",
        "allowed_pipeline", "blocked_pipeline",
        "invariant_with_group", "failure", "replay_hash",
    ):
        assert hasattr(r, f), f


def test_two_runs_produce_identical_replay_hashes() -> None:
    a = FrameInvarianceRunner().run()
    b = FrameInvarianceRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case_id


def test_every_failure_value_is_in_closed_enum() -> None:
    run = FrameInvarianceRunner().run()
    closed = set(FrameInvarianceFailure)
    for r in run.results:
        assert r.failure in closed


def test_every_detected_frame_in_FrameKind_enum() -> None:
    run = FrameInvarianceRunner().run()
    closed = set(FrameKind)
    for r in run.results:
        assert r.detected_frame in closed


def test_invariance_flag_consistent_within_group() -> None:
    """Every result in the same group carries the same flag."""
    run = FrameInvarianceRunner().run()
    by_group: dict[str, list[bool]] = {}
    for r in run.results:
        by_group.setdefault(r.group_id, []).append(r.invariant_with_group)
    for gid, flags in by_group.items():
        assert len(set(flags)) == 1, (
            f"{gid}: inconsistent invariance flags {flags}"
        )


def test_negative_controls_all_distinguished() -> None:
    """Aufgabe 7 success criterion: each negative-control pair must
    produce two distinct detected frames."""
    run = FrameInvarianceRunner().run()
    not_distinguished = [
        nc for nc in run.negative_controls if not nc.distinguished
    ]
    assert not not_distinguished, (
        f"{len(not_distinguished)} negative-controls collapsed to "
        "a single frame"
    )
