"""Tests for the 5 new v1.2 logical-audit ledger event types."""
from __future__ import annotations

import json
import pathlib

from desi.evolution import (
    EvolutionLedger,
    EvolutionLedgerJSONL,
    LedgerEventType,
)
from desi.logic import LogicalAuditor


# ---------------------------------------------------------------------------
# Enum membership
# ---------------------------------------------------------------------------


def test_five_v12_events_in_enum() -> None:
    values = {e.value for e in LedgerEventType}
    for v in (
        "logical_audit_started",
        "logical_gap_detected",
        "logical_bridge_created",
        "logical_proof_accepted",
        "logical_proof_rejected",
    ):
        assert v in values


def test_v11_events_still_present() -> None:
    """Adding the v1.2 events must not remove any v1.1 events."""
    values = {e.value for e in LedgerEventType}
    for v in ("source_document_parsed", "llm_request_started",
              "llm_request_failed", "llm_response_accepted",
              "llm_response_rejected"):
        assert v in values


# ---------------------------------------------------------------------------
# Auditor wires the lifecycle events
# ---------------------------------------------------------------------------


def test_supported_audit_writes_started_and_proof_accepted() -> None:
    led = EvolutionLedger(version="v1.2")
    LogicalAuditor(ledger=led).audit(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    started = led.filter(LedgerEventType.LOGICAL_AUDIT_STARTED)
    accepted = led.filter(LedgerEventType.LOGICAL_PROOF_ACCEPTED)
    assert len(started) == 1
    assert len(accepted) == 1
    assert accepted[0].payload["rule"] == "syllogism"
    assert accepted[0].payload["replay_hash"].startswith("rh_")


def test_rejected_audit_writes_proof_rejected() -> None:
    led = EvolutionLedger(version="v1.2")
    LogicalAuditor(ledger=led).audit("a -> b. b -> c. Therefore a -> d.")
    rejected = led.filter(LedgerEventType.LOGICAL_PROOF_REJECTED)
    assert len(rejected) == 1
    assert rejected[0].payload["reason"] == "unreachable"


def test_authority_audit_writes_proof_rejected() -> None:
    """v1.8: authority audits are no longer a "gap"; they are an
    unconditional rejection. The auditor writes
    LOGICAL_PROOF_REJECTED with reason="authority_claim"."""
    led = EvolutionLedger(version="v1.8")
    LogicalAuditor(ledger=led).audit(
        "Professor X says quantum gravity is solved."
    )
    rejected = led.filter(LedgerEventType.LOGICAL_PROOF_REJECTED)
    assert len(rejected) == 1
    assert rejected[0].payload["reason"] == "authority_claim"
    # And no GAP_DETECTED was emitted for this audit.
    assert led.filter(LedgerEventType.LOGICAL_GAP_DETECTED) == []


def test_bridge_audit_writes_bridge_created() -> None:
    led = EvolutionLedger(version="v1.2")
    LogicalAuditor(ledger=led).audit(
        "It is raining. Therefore the street is wet."
    )
    created = led.filter(LedgerEventType.LOGICAL_BRIDGE_CREATED)
    assert len(created) == 1
    assert created[0].payload["bridge_text"] == \
        "the street is exposed to the rain"


# ---------------------------------------------------------------------------
# JSONL persistence + replay
# ---------------------------------------------------------------------------


def test_jsonl_persists_logical_events(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v1.2")
    LogicalAuditor(ledger=led).audit(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    lines = p.read_text().splitlines()
    assert len(lines) >= 2
    for line in lines:
        rec = json.loads(line)
        assert rec["event_type"].startswith("logical_")


def test_jsonl_logical_events_replay_on_reopen(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "ledger.jsonl"
    led_a = EvolutionLedgerJSONL(p, version="v1.2")
    LogicalAuditor(ledger=led_a).audit(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    n_before = len(led_a.entries())
    led_b = EvolutionLedgerJSONL(p, version="v1.2")
    assert len(led_b.entries()) == n_before


def test_logical_events_have_deterministic_payload_hash(
    tmp_path: pathlib.Path,
) -> None:
    a = EvolutionLedgerJSONL(tmp_path / "a.jsonl", version="v1.2")
    b = EvolutionLedgerJSONL(tmp_path / "b.jsonl", version="v1.2")
    payload = {
        "audit_id": "ac_x",
        "rule": "syllogism",
        "replay_hash": "rh_deadbeef00000000",
        "premise_ids": ["pr_a", "pr_b"],
    }
    ea = a.append(LedgerEventType.LOGICAL_PROOF_ACCEPTED, payload)
    eb = b.append(LedgerEventType.LOGICAL_PROOF_ACCEPTED, payload)
    assert ea.payload_hash == eb.payload_hash
