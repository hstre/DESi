"""Tests for v1.3 INV-C4 / INV-C5 — replay_hash determinism."""
from __future__ import annotations

import time

import pytest

from desi.consilium import (
    BridgeConsilium,
    ConsiliumReplay,
    Verdict,
)
from desi.logic import LogicalAuditor


@pytest.fixture
def rain_audit():
    return LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )


# ---------------------------------------------------------------------------
# Direct API determinism
# ---------------------------------------------------------------------------


def test_replay_hash_is_deterministic() -> None:
    a = ConsiliumReplay(
        bridge_text="the street is exposed to the rain",
        source_claim_id="ac_x",
        verdict=Verdict.ACCEPT_AS_BRIDGE,
        premise_ids=("pr_a", "pr_b"),
        conditions=(),
    )
    b = ConsiliumReplay(
        bridge_text="the street is exposed to the rain",
        source_claim_id="ac_x",
        verdict=Verdict.ACCEPT_AS_BRIDGE,
        premise_ids=("pr_a", "pr_b"),
        conditions=(),
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_is_independent_of_premise_order() -> None:
    a = ConsiliumReplay(
        bridge_text="x", source_claim_id="s", verdict=Verdict.ACCEPT_AS_BRIDGE,
        premise_ids=("pr_a", "pr_b"),
    )
    b = ConsiliumReplay(
        bridge_text="x", source_claim_id="s", verdict=Verdict.ACCEPT_AS_BRIDGE,
        premise_ids=("pr_b", "pr_a"),
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_is_independent_of_condition_order() -> None:
    a = ConsiliumReplay(
        bridge_text="x", source_claim_id="s", verdict=Verdict.ACCEPT_AS_BRIDGE,
        conditions=("alpha", "beta"),
    )
    b = ConsiliumReplay(
        bridge_text="x", source_claim_id="s", verdict=Verdict.ACCEPT_AS_BRIDGE,
        conditions=("beta", "alpha"),
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_changes_with_verdict() -> None:
    a = ConsiliumReplay(bridge_text="x", source_claim_id="s",
                          verdict=Verdict.ACCEPT_AS_BRIDGE)
    b = ConsiliumReplay(bridge_text="x", source_claim_id="s",
                          verdict=Verdict.VETO)
    assert a.replay_hash != b.replay_hash


def test_replay_hash_changes_with_bridge_text() -> None:
    a = ConsiliumReplay(bridge_text="x", source_claim_id="s",
                          verdict=Verdict.ACCEPT_AS_BRIDGE)
    b = ConsiliumReplay(bridge_text="y", source_claim_id="s",
                          verdict=Verdict.ACCEPT_AS_BRIDGE)
    assert a.replay_hash != b.replay_hash


def test_replay_hash_is_independent_of_whitespace() -> None:
    a = ConsiliumReplay(bridge_text="hello world",
                          source_claim_id="s",
                          verdict=Verdict.ACCEPT_AS_BRIDGE)
    b = ConsiliumReplay(bridge_text="  hello   world  ",
                          source_claim_id="s",
                          verdict=Verdict.ACCEPT_AS_BRIDGE)
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# Orchestrator determinism
# ---------------------------------------------------------------------------


def test_two_audits_same_input_same_replay_hash(rain_audit) -> None:
    a = BridgeConsilium().deliberate(
        rain_audit.bridges[0],
        source_claim_id=rain_audit.audit_id,
        original_text=rain_audit.text,
    )
    b = BridgeConsilium().deliberate(
        rain_audit.bridges[0],
        source_claim_id=rain_audit.audit_id,
        original_text=rain_audit.text,
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_wall_clock(rain_audit) -> None:
    a = BridgeConsilium().deliberate(
        rain_audit.bridges[0],
        source_claim_id=rain_audit.audit_id,
        original_text=rain_audit.text,
    )
    time.sleep(0.01)
    b = BridgeConsilium().deliberate(
        rain_audit.bridges[0],
        source_claim_id=rain_audit.audit_id,
        original_text=rain_audit.text,
    )
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# INV-C5: same bridge text + same premises → identical verdict
# ---------------------------------------------------------------------------


def test_same_bridge_text_same_premises_same_verdict(rain_audit) -> None:
    cons = BridgeConsilium()
    a = cons.deliberate(
        rain_audit.bridges[0],
        source_claim_id=rain_audit.audit_id,
        original_text=rain_audit.text,
    )
    b = cons.deliberate(
        rain_audit.bridges[0],
        source_claim_id=rain_audit.audit_id,
        original_text=rain_audit.text,
    )
    assert a.verdict.verdict == b.verdict.verdict
