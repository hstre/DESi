"""Tests for v2.2 DepthEvolutionReport replay-hash determinism."""
from __future__ import annotations

from desi.sandbox import compute_depth_replay_hash
from desi.sandbox.depth_report import (
    detect_convergence,
    detect_oscillation,
)


def test_replay_hash_is_sixteen_hex_chars() -> None:
    h = compute_depth_replay_hash({"total_steps": 30, "best_depth": 3})
    assert len(h) == 16
    int(h, 16)


def test_replay_hash_independent_of_timestamps() -> None:
    a = compute_depth_replay_hash({
        "started_at": "2026-01-01", "finished_at": "2026-01-02",
        "total_steps": 30,
    })
    b = compute_depth_replay_hash({
        "started_at": "2030-12-31", "finished_at": "2031-01-01",
        "total_steps": 30,
    })
    assert a == b


def test_replay_hash_excludes_replay_hash_field() -> None:
    a = compute_depth_replay_hash({"total_steps": 30, "replay_hash": "a"})
    b = compute_depth_replay_hash({"total_steps": 30, "replay_hash": "b"})
    assert a == b


def test_replay_hash_differs_when_payload_differs() -> None:
    a = compute_depth_replay_hash({"total_steps": 30})
    b = compute_depth_replay_hash({"total_steps": 31})
    assert a != b


def test_oscillation_detected_in_zigzag() -> None:
    assert detect_oscillation([3, 4, 3, 4, 3]) is True


def test_oscillation_not_detected_in_monotonic() -> None:
    assert detect_oscillation([3, 4, 5, 6]) is False


def test_convergence_detected_in_flat_tail() -> None:
    assert detect_convergence([3, 3, 3, 3, 3], window=5) is True


def test_convergence_not_detected_when_moving() -> None:
    assert detect_convergence([3, 4, 5, 6, 7], window=5) is False
