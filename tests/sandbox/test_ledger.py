"""Tests for the v2.0 ShadowLedger (Aufgabe 4)."""
from __future__ import annotations

import json
import pathlib

from desi.sandbox import ShadowLedger, ShadowLedgerEventType


def test_event_type_enum_is_eight_values() -> None:
    assert len(list(ShadowLedgerEventType)) == 8


def test_event_type_set_is_closed_and_named() -> None:
    expected = {
        "sandbox_started",
        "mutation_proposed",
        "mutation_applied",
        "benchmark_started",
        "benchmark_completed",
        "mutation_accepted",
        "mutation_rejected",
        "sandbox_completed",
    }
    assert {e.value for e in ShadowLedgerEventType} == expected


def test_append_returns_entry_with_canonical_hash() -> None:
    ledger = ShadowLedger()
    entry = ledger.append(
        ShadowLedgerEventType.SANDBOX_STARTED,
        {"step_id": 1, "version": "stable-v1.9.0"},
    )
    assert entry.event_type is ShadowLedgerEventType.SANDBOX_STARTED
    assert entry.ledger_id.startswith("sl_")
    assert len(entry.payload_hash) == 16


def test_payload_hash_is_deterministic_across_key_order() -> None:
    a = ShadowLedger().append(
        ShadowLedgerEventType.MUTATION_PROPOSED,
        {"a": 1, "b": 2, "c": [3, 4]},
    )
    b = ShadowLedger().append(
        ShadowLedgerEventType.MUTATION_PROPOSED,
        {"c": [3, 4], "b": 2, "a": 1},
    )
    assert a.payload_hash == b.payload_hash


def test_append_is_in_order_and_monotonic() -> None:
    ledger = ShadowLedger()
    for i in range(5):
        ledger.append(
            ShadowLedgerEventType.MUTATION_APPLIED, {"step_id": i},
        )
    ids = [e.payload["step_id"] for e in ledger.entries()]
    assert ids == [0, 1, 2, 3, 4]
    assert len(ledger) == 5


def test_filter_returns_only_matching_event_type() -> None:
    ledger = ShadowLedger()
    ledger.append(
        ShadowLedgerEventType.MUTATION_PROPOSED, {"step_id": 1},
    )
    ledger.append(
        ShadowLedgerEventType.MUTATION_APPLIED, {"step_id": 1},
    )
    ledger.append(
        ShadowLedgerEventType.MUTATION_PROPOSED, {"step_id": 2},
    )
    proposed = ledger.filter(ShadowLedgerEventType.MUTATION_PROPOSED)
    assert len(proposed) == 2
    assert all(
        e.event_type is ShadowLedgerEventType.MUTATION_PROPOSED
        for e in proposed
    )


def test_persistence_round_trip(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "shadow.jsonl"
    a = ShadowLedger(path=p)
    a.append(ShadowLedgerEventType.SANDBOX_STARTED, {"v": "x"})
    a.append(ShadowLedgerEventType.SANDBOX_COMPLETED, {"v": "x"})
    # Re-open and replay.
    b = ShadowLedger(path=p)
    assert len(b) == 2
    assert b.entries()[0].event_type is ShadowLedgerEventType.SANDBOX_STARTED
    assert b.entries()[1].event_type is ShadowLedgerEventType.SANDBOX_COMPLETED


def test_file_is_append_only_jsonl(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "shadow.jsonl"
    led = ShadowLedger(path=p)
    led.append(ShadowLedgerEventType.SANDBOX_STARTED, {"step": 1})
    led.append(ShadowLedgerEventType.MUTATION_PROPOSED, {"step": 1})
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    for raw in lines:
        rec = json.loads(raw)
        assert "ledger_id" in rec
        assert "event_type" in rec
        assert "payload" in rec
        assert "payload_hash" in rec
