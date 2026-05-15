"""Tests for v2.1 SelfDiagnosticReport replay-hash determinism."""
from __future__ import annotations

from desi.diagnostic import compute_report_replay_hash


def test_replay_hash_is_sixteen_hex_chars() -> None:
    h = compute_report_replay_hash({"total_deficits": 0})
    assert len(h) == 16
    int(h, 16)


def test_replay_hash_independent_of_timestamps() -> None:
    a = compute_report_replay_hash({
        "started_at": "2026-01-01", "finished_at": "2026-01-02",
        "total_deficits": 3,
    })
    b = compute_report_replay_hash({
        "started_at": "2030-12-31", "finished_at": "2031-01-01",
        "total_deficits": 3,
    })
    assert a == b


def test_replay_hash_ignores_its_own_field() -> None:
    a = compute_report_replay_hash({"total_deficits": 3, "replay_hash": "x"})
    b = compute_report_replay_hash({"total_deficits": 3, "replay_hash": "y"})
    assert a == b


def test_replay_hash_changes_when_payload_changes() -> None:
    a = compute_report_replay_hash({"total_deficits": 3})
    b = compute_report_replay_hash({"total_deficits": 4})
    assert a != b


def test_replay_hash_invariant_under_key_order() -> None:
    a = compute_report_replay_hash({"a": 1, "b": 2, "c": 3})
    b = compute_report_replay_hash({"c": 3, "b": 2, "a": 1})
    assert a == b
