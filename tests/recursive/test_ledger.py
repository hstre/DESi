"""Tests for the 7 new v1.4 recursive ledger event types."""
from __future__ import annotations

import json
import pathlib

from desi.consilium import Verdict
from desi.evolution import (
    EvolutionLedger,
    EvolutionLedgerJSONL,
    LedgerEventType,
)
from desi.recursive import RecursiveResolver

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    needs_bridge,
)


# ---------------------------------------------------------------------------
# Enum membership
# ---------------------------------------------------------------------------


def test_seven_v14_events_in_enum() -> None:
    values = {e.value for e in LedgerEventType}
    for v in (
        "recursive_resolution_started",
        "recursive_node_entered",
        "recursive_node_resolved",
        "recursive_node_blocked",
        "recursive_cycle_detected",
        "recursive_depth_exceeded",
        "recursive_resolution_completed",
    ):
        assert v in values


def test_v13_consilium_events_still_present() -> None:
    """v1.4 must not remove any v1.3 ledger event."""
    values = {e.value for e in LedgerEventType}
    for v in ("consilium_started", "consilium_role_reviewed",
              "consilium_counterexample_found", "consilium_veto",
              "consilium_accepted", "consilium_rejected",
              "claim_upgraded_by_consilium"):
        assert v in values


# ---------------------------------------------------------------------------
# COMPLETE path emits started + node_entered + node_resolved + completed
# ---------------------------------------------------------------------------


def test_complete_path_writes_started_and_completed() -> None:
    led = EvolutionLedger(version="v1.4")
    RecursiveResolver(ledger=led).resolve(
        "It is raining. Therefore the street is wet."
    )
    started = led.filter(LedgerEventType.RECURSIVE_RESOLUTION_STARTED)
    completed = led.filter(LedgerEventType.RECURSIVE_RESOLUTION_COMPLETED)
    assert len(started) == 1
    assert len(completed) == 1
    assert completed[0].payload["final_state"] == "resolution_complete"


def test_complete_path_writes_node_entered_for_every_node() -> None:
    led = EvolutionLedger(version="v1.4")
    RecursiveResolver(ledger=led).resolve(
        "It is raining. Therefore the street is wet."
    )
    entered = led.filter(LedgerEventType.RECURSIVE_NODE_ENTERED)
    # Root + bridge → at least 2 entries.
    assert len(entered) >= 2


# ---------------------------------------------------------------------------
# Cycle path emits cycle event + completed
# ---------------------------------------------------------------------------


def test_cycle_writes_cycle_detected_event() -> None:
    led = EvolutionLedger(version="v1.4")
    auditor = ScriptedAuditor(script={
        "a": needs_bridge("a", "b"),
        "b": needs_bridge("b", "a"),
    })
    RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(), ledger=led,
    ).resolve("a")
    cycle = led.filter(LedgerEventType.RECURSIVE_CYCLE_DETECTED)
    assert len(cycle) == 1
    assert "cycle_path" in cycle[0].payload


# ---------------------------------------------------------------------------
# Depth-exceeded emits depth event + completed
# ---------------------------------------------------------------------------


def test_depth_exceeded_writes_depth_event() -> None:
    led = EvolutionLedger(version="v1.4")
    auditor = ScriptedAuditor(script={
        "n0": needs_bridge("n0", "n1"),
        "n1": needs_bridge("n1", "n2"),
        "n2": needs_bridge("n2", "n3"),
        "n3": needs_bridge("n3", "n4"),
    })
    RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(), ledger=led,
    ).resolve("n0", max_depth=2)
    depth = led.filter(LedgerEventType.RECURSIVE_DEPTH_EXCEEDED)
    assert len(depth) >= 1
    assert depth[0].payload["max_depth"] == 2


# ---------------------------------------------------------------------------
# Block path emits node_blocked
# ---------------------------------------------------------------------------


def test_blocked_path_writes_node_blocked() -> None:
    led = EvolutionLedger(version="v1.4")
    auditor = ScriptedAuditor(script={
        "root": needs_bridge("root", "child"),
    })
    cons = ScriptedConsilium(blocked_bridges={"child": Verdict.VETO})
    RecursiveResolver(
        auditor=auditor, consilium=cons, ledger=led,
    ).resolve("root")
    blocked = led.filter(LedgerEventType.RECURSIVE_NODE_BLOCKED)
    assert len(blocked) >= 1


# ---------------------------------------------------------------------------
# JSONL persistence + replay
# ---------------------------------------------------------------------------


def test_jsonl_persists_recursive_events(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v1.4")
    RecursiveResolver(ledger=led).resolve(
        "It is raining. Therefore the street is wet."
    )
    lines = p.read_text().splitlines()
    assert lines
    # At least one line is a v1.4 event.
    types = [json.loads(line)["event_type"] for line in lines]
    assert any(t.startswith("recursive_") for t in types)


def test_jsonl_recursive_events_replay_on_reopen(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "ledger.jsonl"
    led_a = EvolutionLedgerJSONL(p, version="v1.4")
    RecursiveResolver(ledger=led_a).resolve(
        "It is raining. Therefore the street is wet."
    )
    n_before = len(led_a.entries())
    led_b = EvolutionLedgerJSONL(p, version="v1.4")
    assert len(led_b.entries()) == n_before


def test_recursive_events_have_deterministic_payload_hash(
    tmp_path: pathlib.Path,
) -> None:
    a = EvolutionLedgerJSONL(tmp_path / "a.jsonl", version="v1.4")
    b = EvolutionLedgerJSONL(tmp_path / "b.jsonl", version="v1.4")
    payload = {
        "root_claim_id": "rn_x",
        "final_state": "resolution_complete",
        "depth_reached": 1,
        "replay_hash": "rr_deadbeefcafef00d",
        "n_resolved": 2,
        "n_blocked": 0,
    }
    ea = a.append(LedgerEventType.RECURSIVE_RESOLUTION_COMPLETED, payload)
    eb = b.append(LedgerEventType.RECURSIVE_RESOLUTION_COMPLETED, payload)
    assert ea.payload_hash == eb.payload_hash
