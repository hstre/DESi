"""Aufgaben 3 + 6 — closed enums + ledger event set."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.frame_tension import (
    FrameConsistency,
    FrameTensionLedger,
    FrameTensionLedgerEvent,
)


def test_frame_consistency_has_four_values() -> None:
    assert len(list(FrameConsistency)) == 4


def test_frame_consistency_values() -> None:
    assert {c.value for c in FrameConsistency} == {
        "confirmed",
        "tension",
        "conflict",
        "undecidable",
    }


def test_ledger_event_has_four_values() -> None:
    assert len(list(FrameTensionLedgerEvent)) == 4


def test_ledger_event_values() -> None:
    assert {e.value for e in FrameTensionLedgerEvent} == {
        "frame_inheritance_allowed",
        "frame_inheritance_blocked",
        "frame_conflict_blocked",
        "frame_undecidable_blocked",
    }


def test_ledger_append_assigns_sequential_ids() -> None:
    led = FrameTensionLedger()
    when = datetime.now(timezone.utc)
    a = led.append(
        event=FrameTensionLedgerEvent.FRAME_INHERITANCE_ALLOWED,
        claim_id="c1", inner_frame="thermodynamic",
        outer_frame="thermodynamic",
        consistency="confirmed", recorded_at=when,
    )
    b = led.append(
        event=FrameTensionLedgerEvent.FRAME_INHERITANCE_BLOCKED,
        claim_id="c2", inner_frame="information_theoretic",
        outer_frame="thermodynamic",
        consistency="tension", recorded_at=when,
    )
    assert a.event_id == "ftl_000000"
    assert b.event_id == "ftl_000001"
    assert len(led.entries) == 2


def test_ledger_payload_hash_is_deterministic() -> None:
    when = datetime(2026, 1, 1, tzinfo=timezone.utc)
    a = FrameTensionLedger().append(
        event=FrameTensionLedgerEvent.FRAME_CONFLICT_BLOCKED,
        claim_id="c1", inner_frame="formal_logic",
        outer_frame="tool_computable",
        consistency="conflict", recorded_at=when,
    )
    b = FrameTensionLedger().append(
        event=FrameTensionLedgerEvent.FRAME_CONFLICT_BLOCKED,
        claim_id="c1", inner_frame="formal_logic",
        outer_frame="tool_computable",
        consistency="conflict", recorded_at=when,
    )
    assert a.payload_hash == b.payload_hash
