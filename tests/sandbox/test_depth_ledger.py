"""Tests for the v2.2 DepthShadowLedger (Aufgabe 7)."""
from __future__ import annotations

import pathlib

from desi.sandbox import DepthLedgerEventType, DepthShadowLedger


_EXPECTED_EVENTS = {
    "depth_mutation_proposed",
    "depth_mutation_applied",
    "depth_stress_started",
    "depth_stress_completed",
    "depth_mutation_accepted",
    "depth_mutation_rejected",
}


def test_six_event_types_exactly() -> None:
    assert len(list(DepthLedgerEventType)) == 6


def test_event_type_set_matches_directive() -> None:
    assert {e.value for e in DepthLedgerEventType} == _EXPECTED_EVENTS


def test_append_returns_entry_with_hash() -> None:
    ledger = DepthShadowLedger()
    entry = ledger.append(
        DepthLedgerEventType.DEPTH_MUTATION_PROPOSED,
        {"step_id": 1, "proposed_depth": 4},
    )
    assert entry.event_type is DepthLedgerEventType.DEPTH_MUTATION_PROPOSED
    assert entry.ledger_id.startswith("dl_")
    assert len(entry.payload_hash) == 16


def test_payload_hash_is_canonical() -> None:
    """Same payload in different key order → same hash."""
    a = DepthShadowLedger().append(
        DepthLedgerEventType.DEPTH_MUTATION_APPLIED,
        {"step_id": 1, "proposed_depth": 4, "clone_hash": "x"},
    )
    b = DepthShadowLedger().append(
        DepthLedgerEventType.DEPTH_MUTATION_APPLIED,
        {"clone_hash": "x", "proposed_depth": 4, "step_id": 1},
    )
    assert a.payload_hash == b.payload_hash


def test_filter_returns_only_matching_event_type() -> None:
    led = DepthShadowLedger()
    led.append(
        DepthLedgerEventType.DEPTH_MUTATION_PROPOSED, {"step_id": 1},
    )
    led.append(
        DepthLedgerEventType.DEPTH_MUTATION_APPLIED, {"step_id": 1},
    )
    led.append(
        DepthLedgerEventType.DEPTH_MUTATION_PROPOSED, {"step_id": 2},
    )
    proposed = led.filter(DepthLedgerEventType.DEPTH_MUTATION_PROPOSED)
    assert len(proposed) == 2


def test_append_is_in_order() -> None:
    led = DepthShadowLedger()
    for i in range(4):
        led.append(
            DepthLedgerEventType.DEPTH_MUTATION_APPLIED, {"step_id": i},
        )
    ids = [e.payload["step_id"] for e in led.entries()]
    assert ids == [0, 1, 2, 3]


def test_persistence_round_trip(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "depth.jsonl"
    a = DepthShadowLedger(path=p)
    a.append(DepthLedgerEventType.DEPTH_STRESS_STARTED, {"v": "x"})
    a.append(DepthLedgerEventType.DEPTH_STRESS_COMPLETED, {"v": "y"})
    b = DepthShadowLedger(path=p)
    assert len(b) == 2
    assert (b.entries()[0].event_type
            is DepthLedgerEventType.DEPTH_STRESS_STARTED)


def test_v20_ledger_event_types_not_in_v22() -> None:
    """v2.0 and v2.2 enums are independent — no cross-pollination."""
    from desi.sandbox import ShadowLedgerEventType
    overlap = (
        {e.value for e in DepthLedgerEventType}
        & {e.value for e in ShadowLedgerEventType}
    )
    assert overlap == set(), f"event-type leak between v2.0 and v2.2: {overlap}"
