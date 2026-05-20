"""Tests for EvolutionLedger — append-only semantics + exports."""
from __future__ import annotations

import json

import pytest

from desi.evolution import EvolutionLedger, LedgerEntry, LedgerEventType


# ---------------------------------------------------------------------------
# Basic append + read
# ---------------------------------------------------------------------------


def test_ledger_starts_empty() -> None:
    ledger = EvolutionLedger()
    assert len(ledger) == 0
    assert ledger.entries() == ()


def test_append_creates_entry_with_required_fields() -> None:
    ledger = EvolutionLedger()
    entry = ledger.append(LedgerEventType.REFLECTION,
                          {"evaluation_id": "eval_x"})
    assert isinstance(entry, LedgerEntry)
    assert entry.ledger_id.startswith("le_")
    assert entry.event_type is LedgerEventType.REFLECTION
    assert entry.payload == {"evaluation_id": "eval_x"}
    assert entry.payload_hash  # non-empty
    assert entry.version == "v0.6"


def test_append_preserves_insertion_order() -> None:
    ledger = EvolutionLedger()
    a = ledger.append(LedgerEventType.REFLECTION, {"x": 1})
    b = ledger.append(LedgerEventType.PROPOSAL, {"y": 2})
    c = ledger.append(LedgerEventType.EVALUATION, {"z": 3})
    assert ledger.entries() == (a, b, c)


# ---------------------------------------------------------------------------
# Append-only invariant
# ---------------------------------------------------------------------------


def test_ledger_entries_returns_an_immutable_tuple() -> None:
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.REFLECTION, {"a": 1})
    snap = ledger.entries()
    assert isinstance(snap, tuple)
    # Tuples have no append method; explicit guard.
    with pytest.raises(AttributeError):
        snap.append("nope")  # type: ignore[attr-defined]


def test_existing_entries_never_change_when_new_one_is_appended() -> None:
    ledger = EvolutionLedger()
    first = ledger.append(LedgerEventType.REFLECTION, {"a": 1})
    baseline = ledger.entries()
    for _ in range(5):
        ledger.append(LedgerEventType.PROPOSAL, {"b": 2})
    # The first entry must be byte-equal to the original snapshot.
    assert ledger.entries()[0] == first
    assert ledger.verify_append_only(baseline)


def test_verify_append_only_detects_a_diverged_baseline() -> None:
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.REFLECTION, {"a": 1})
    snap = ledger.entries()
    # Hand-craft a forged baseline of length 1 with a different payload
    # hash; verify_append_only must reject it.
    forged = (LedgerEntry(
        ledger_id="le_forged",
        event_type=LedgerEventType.PROPOSAL,
        timestamp=snap[0].timestamp,
        parent_event_id=None,
        payload_hash="forged_hash",
        payload={"x": 999},
        actor="attacker",
        version="v0.6",
    ),)
    assert ledger.verify_append_only(forged) is False


# ---------------------------------------------------------------------------
# Deterministic payload hashing
# ---------------------------------------------------------------------------


def test_two_ledgers_produce_same_payload_hash_for_same_payload() -> None:
    a = EvolutionLedger().append(LedgerEventType.PROPOSAL,
                                  {"mutation_id": "mut_1", "x": 1})
    b = EvolutionLedger().append(LedgerEventType.PROPOSAL,
                                  {"mutation_id": "mut_1", "x": 1})
    assert a.payload_hash == b.payload_hash


def test_payload_hash_changes_when_payload_changes() -> None:
    a = EvolutionLedger().append(LedgerEventType.PROPOSAL, {"x": 1})
    b = EvolutionLedger().append(LedgerEventType.PROPOSAL, {"x": 2})
    assert a.payload_hash != b.payload_hash


# ---------------------------------------------------------------------------
# Filter + find_one
# ---------------------------------------------------------------------------


def test_filter_by_event_type() -> None:
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.REFLECTION, {"a": 1})
    p = ledger.append(LedgerEventType.PROPOSAL, {"b": 2})
    ledger.append(LedgerEventType.REFLECTION, {"c": 3})
    only_proposals = ledger.filter(LedgerEventType.PROPOSAL)
    assert len(only_proposals) == 1
    assert only_proposals[0] is p


def test_filter_by_parent_event_id() -> None:
    ledger = EvolutionLedger()
    parent = ledger.append(LedgerEventType.PROPOSAL, {"id": "mut_1"})
    child = ledger.append(
        LedgerEventType.EVALUATION,
        {"mutation_id": "mut_1"},
        parent_event_id=parent.ledger_id,
    )
    found = ledger.filter(parent_event_id=parent.ledger_id)
    assert found == [child]


def test_find_one_returns_matching_entry_or_none() -> None:
    ledger = EvolutionLedger()
    e = ledger.append(LedgerEventType.PROPOSAL, {"x": 1})
    assert ledger.find_one(e.ledger_id) is e
    assert ledger.find_one("le_does_not_exist") is None


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------


def test_to_json_round_trips_entries() -> None:
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.REFLECTION, {"a": 1})
    ledger.append(LedgerEventType.PROPOSAL, {"mutation_id": "mut_1"})
    doc = json.loads(ledger.to_json())
    assert doc["entry_count"] == 2
    assert doc["entries"][0]["event_type"] == "reflection"
    assert doc["entries"][1]["payload"]["mutation_id"] == "mut_1"


def test_to_markdown_is_a_table_with_one_row_per_entry() -> None:
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.REFLECTION, {"a": 1})
    ledger.append(LedgerEventType.PROPOSAL, {"b": 2})
    md = ledger.to_markdown()
    # Header + separator + 2 data rows.
    rows = [line for line in md.splitlines() if line.startswith("|")]
    assert len(rows) == 4
    assert "reflection" in md
    assert "proposal" in md


def test_payload_normalisation_handles_enums_and_datetimes() -> None:
    """Payloads carrying enums / datetimes must serialise cleanly."""
    from datetime import datetime, timezone
    ledger = EvolutionLedger()
    ledger.append(LedgerEventType.PROPOSAL, {
        "ts": datetime(2026, 5, 14, tzinfo=timezone.utc),
        "kind": LedgerEventType.PROPOSAL,
    })
    payload = json.loads(ledger.to_json())["entries"][0]["payload"]
    assert payload["ts"].startswith("2026-05-14")
    assert payload["kind"] == "proposal"
