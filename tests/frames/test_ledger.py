"""Tests for FrameLedger — Aufgaben 7 + 10."""
from __future__ import annotations

import pathlib

from desi.frames import FrameLedger, FrameLedgerEventType


_EXPECTED = {
    "frame_declaration_started", "frame_declared",
    "frame_undeclared", "frame_conflict_detected",
    "frame_compatibility_checked", "frame_pipeline_blocked",
}


def test_six_frame_event_types_exactly() -> None:
    assert len(list(FrameLedgerEventType)) == 6
    assert {e.value for e in FrameLedgerEventType} == _EXPECTED


def test_append_returns_entry_with_payload_hash() -> None:
    ledger = FrameLedger()
    entry = ledger.append(
        FrameLedgerEventType.FRAME_DECLARED,
        {"claim_id": "c", "frame_kind": "thermodynamic"},
    )
    assert entry.event_type is FrameLedgerEventType.FRAME_DECLARED
    assert entry.ledger_id.startswith("fl_")
    assert len(entry.payload_hash) == 16


def test_payload_hash_invariant_under_key_order() -> None:
    a = FrameLedger().append(
        FrameLedgerEventType.FRAME_COMPATIBILITY_CHECKED,
        {"a": 1, "b": 2, "c": [3, 4]},
    )
    b = FrameLedger().append(
        FrameLedgerEventType.FRAME_COMPATIBILITY_CHECKED,
        {"c": [3, 4], "b": 2, "a": 1},
    )
    assert a.payload_hash == b.payload_hash


def test_filter_returns_only_matching_event_type() -> None:
    ledger = FrameLedger()
    ledger.append(FrameLedgerEventType.FRAME_DECLARED, {"v": 1})
    ledger.append(FrameLedgerEventType.FRAME_CONFLICT_DETECTED, {"v": 2})
    ledger.append(FrameLedgerEventType.FRAME_DECLARED, {"v": 3})
    declared = ledger.filter(FrameLedgerEventType.FRAME_DECLARED)
    assert len(declared) == 2


def test_persistence_round_trip(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "frames.jsonl"
    a = FrameLedger(path=p)
    a.append(FrameLedgerEventType.FRAME_DECLARATION_STARTED, {"x": 1})
    a.append(FrameLedgerEventType.FRAME_PIPELINE_BLOCKED, {"x": 2})
    b = FrameLedger(path=p)
    assert len(b) == 2
    assert (b.entries()[0].event_type
            is FrameLedgerEventType.FRAME_DECLARATION_STARTED)


def test_v22_v20_v34_event_type_sets_disjoint() -> None:
    """Three sandbox-style ledgers must not collide on event names."""
    from desi.sandbox import DepthLedgerEventType, ShadowLedgerEventType
    v20 = {e.value for e in ShadowLedgerEventType}
    v22 = {e.value for e in DepthLedgerEventType}
    v34 = {e.value for e in FrameLedgerEventType}
    assert v20.isdisjoint(v22)
    assert v20.isdisjoint(v34)
    assert v22.isdisjoint(v34)
