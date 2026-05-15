"""Tests for v2.8 RulePatchRecord (Aufgabe 2)."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.rule_patch_protocol import (
    PatchPhase,
    PhaseOutcome,
    RulePatchRecord,
    compute_record_replay_hash,
)


def _record(**overrides) -> RulePatchRecord:
    base = dict(
        patch_id="pp_test",
        target_rule="causal_chain",
        source_branch="feature/x",
        phase=PatchPhase.COMPLETE,
        passed=True,
        created_guards=("g1", "g2"),
        touched_files=("src/desi/logic/inference.py",),
        benchmark_hash_before="aa" * 8,
        benchmark_hash_after="aa" * 8,
        replay_hash="0" * 16,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    base.update(overrides)
    return RulePatchRecord(**base)


def test_required_fields_present() -> None:
    rec = _record()
    for f in (
        "patch_id", "target_rule", "source_branch", "phase",
        "passed", "created_guards", "touched_files",
        "benchmark_hash_before", "benchmark_hash_after",
        "replay_hash", "timestamp",
    ):
        assert hasattr(rec, f), f


def test_to_dict_round_trip_shape() -> None:
    rec = _record()
    d = rec.to_dict()
    for k in (
        "patch_id", "target_rule", "source_branch", "phase",
        "passed", "created_guards", "touched_files",
        "benchmark_hash_before", "benchmark_hash_after",
        "replay_hash", "timestamp", "phase_outcomes", "fail_reason",
    ):
        assert k in d


def test_replay_hash_is_sixteen_hex_chars() -> None:
    h = compute_record_replay_hash({"patch_id": "x"})
    assert len(h) == 16
    int(h, 16)


def test_replay_hash_ignores_timestamp() -> None:
    a = compute_record_replay_hash({"p": 1, "timestamp": "2020"})
    b = compute_record_replay_hash({"p": 1, "timestamp": "2030"})
    assert a == b


def test_replay_hash_ignores_its_own_field() -> None:
    a = compute_record_replay_hash({"p": 1, "replay_hash": "x"})
    b = compute_record_replay_hash({"p": 1, "replay_hash": "y"})
    assert a == b


def test_replay_hash_changes_when_payload_changes() -> None:
    a = compute_record_replay_hash({"p": 1})
    b = compute_record_replay_hash({"p": 2})
    assert a != b


def test_phase_outcome_carries_fields() -> None:
    o = PhaseOutcome(
        phase=PatchPhase.DISCOVERY, passed=True, reason="ok",
    )
    d = o.to_dict()
    for k in ("phase", "passed", "reason", "data"):
        assert k in d
