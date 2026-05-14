"""Tests for the 7 new v1.3 consilium ledger event types."""
from __future__ import annotations

import json
import pathlib

from desi.consilium import (
    BridgeConsilium,
)
from desi.evolution import (
    EvolutionLedger,
    EvolutionLedgerJSONL,
    LedgerEventType,
)
from desi.logic import LogicalAuditor


def _rain_bridge():
    return LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )


# ---------------------------------------------------------------------------
# Enum membership
# ---------------------------------------------------------------------------


def test_seven_v13_events_in_enum() -> None:
    values = {e.value for e in LedgerEventType}
    for v in (
        "consilium_started",
        "consilium_role_reviewed",
        "consilium_counterexample_found",
        "consilium_veto",
        "consilium_accepted",
        "consilium_rejected",
        "claim_upgraded_by_consilium",
    ):
        assert v in values


def test_v12_logical_events_still_present() -> None:
    values = {e.value for e in LedgerEventType}
    for v in ("logical_audit_started", "logical_gap_detected",
              "logical_bridge_created", "logical_proof_accepted",
              "logical_proof_rejected"):
        assert v in values


# ---------------------------------------------------------------------------
# Orchestrator writes the lifecycle events
# ---------------------------------------------------------------------------


def test_accept_path_writes_started_role_and_accepted() -> None:
    led = EvolutionLedger(version="v1.3")
    audit = _rain_bridge()
    BridgeConsilium(ledger=led).deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    started = led.filter(LedgerEventType.CONSILIUM_STARTED)
    roles = led.filter(LedgerEventType.CONSILIUM_ROLE_REVIEWED)
    accepted = led.filter(LedgerEventType.CONSILIUM_ACCEPTED)
    assert len(started) >= 1
    assert len(roles) == 4
    assert len(accepted) == 1


def test_veto_path_writes_veto_event() -> None:
    led = EvolutionLedger(version="v1.3")
    audit = _rain_bridge()
    BridgeConsilium(ledger=led).deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
    )
    veto = led.filter(LedgerEventType.CONSILIUM_VETO)
    assert len(veto) == 1
    assert "skeptic" in veto[0].payload["blocking_roles"]


def test_skeptic_hit_writes_counterexample_found_event() -> None:
    led = EvolutionLedger(version="v1.3")
    audit = _rain_bridge()
    BridgeConsilium(ledger=led).deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
    )
    cex = led.filter(LedgerEventType.CONSILIUM_COUNTEREXAMPLE_FOUND)
    assert len(cex) == 1
    assert cex[0].payload["role"] == "skeptic"


def test_hard_reject_writes_rejected_event() -> None:
    led = EvolutionLedger(version="v1.3")
    audit = _rain_bridge()
    BridgeConsilium(ledger=led).deliberate(
        audit.bridges[0],
        source_claim_id="",  # forced empty → REJECT
        original_text=audit.text,
    )
    rejected = led.filter(LedgerEventType.CONSILIUM_REJECTED)
    assert len(rejected) == 1
    assert rejected[0].payload["verdict"] == "reject_bridge"


# ---------------------------------------------------------------------------
# Per-role events carry the role label
# ---------------------------------------------------------------------------


def test_role_reviewed_payload_carries_role_field() -> None:
    led = EvolutionLedger(version="v1.3")
    audit = _rain_bridge()
    BridgeConsilium(ledger=led).deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    roles = led.filter(LedgerEventType.CONSILIUM_ROLE_REVIEWED)
    role_labels = {e.payload["role"] for e in roles}
    assert role_labels == {"logician", "skeptic", "domain_examiner",
                            "integrator"}


# ---------------------------------------------------------------------------
# JSONL persistence + replay
# ---------------------------------------------------------------------------


def test_jsonl_persists_consilium_events(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "ledger.jsonl"
    led = EvolutionLedgerJSONL(p, version="v1.3")
    audit = _rain_bridge()
    BridgeConsilium(ledger=led).deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    lines = p.read_text().splitlines()
    assert lines
    for line in lines:
        rec = json.loads(line)
        assert (rec["event_type"].startswith("consilium_")
                or rec["event_type"] == "claim_upgraded_by_consilium")


def test_jsonl_consilium_events_replay_on_reopen(
    tmp_path: pathlib.Path,
) -> None:
    p = tmp_path / "ledger.jsonl"
    led_a = EvolutionLedgerJSONL(p, version="v1.3")
    audit = _rain_bridge()
    BridgeConsilium(ledger=led_a).deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    n_before = len(led_a.entries())
    led_b = EvolutionLedgerJSONL(p, version="v1.3")
    assert len(led_b.entries()) == n_before


def test_consilium_events_have_deterministic_payload_hash(
    tmp_path: pathlib.Path,
) -> None:
    a = EvolutionLedgerJSONL(tmp_path / "a.jsonl", version="v1.3")
    b = EvolutionLedgerJSONL(tmp_path / "b.jsonl", version="v1.3")
    payload = {
        "bridge_id": "br_x",
        "source_claim_id": "ac_y",
        "replay_hash": "cr_deadbeefcafef00d",
    }
    ea = a.append(LedgerEventType.CONSILIUM_ACCEPTED, payload)
    eb = b.append(LedgerEventType.CONSILIUM_ACCEPTED, payload)
    assert ea.payload_hash == eb.payload_hash
