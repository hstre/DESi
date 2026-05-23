"""Tests for v1.3 bridge state transitions + original-claim upgrade."""
from __future__ import annotations

import pytest

from desi.consilium import (
    BridgeConsilium,
    BridgeState,
    ClaimUpgradeError,
    Verdict,
    promote_accepted_bridge,
    upgrade_original_claim,
)
from desi.logic import LogicalAuditor
from desi.logic.bridge_claims import BRIDGE_METHOD
from desi.memory.claim import Claim, ClaimState, Provenance


def _audit_and_consilium():
    audit = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    res = BridgeConsilium().deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    return audit, res


# ---------------------------------------------------------------------------
# Bridge promotion
# ---------------------------------------------------------------------------


def test_accepted_bridge_promotes_to_logically_supported() -> None:
    audit, res = _audit_and_consilium()
    assert res.verdict.verdict is Verdict.ACCEPT_AS_BRIDGE
    new_claim = promote_accepted_bridge(audit.bridges[0], res.verdict)
    assert new_claim.state is ClaimState.LOGICALLY_SUPPORTED
    assert new_claim.method == BRIDGE_METHOD == "logical_bridge"


def test_promoted_bridge_keeps_content_verbatim() -> None:
    audit, res = _audit_and_consilium()
    new_claim = promote_accepted_bridge(audit.bridges[0], res.verdict)
    assert new_claim.content == audit.bridges[0].claim.content


def test_promotion_refuses_non_accepted_verdict() -> None:
    audit, _ = _audit_and_consilium()
    veto = BridgeConsilium().deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
    )
    with pytest.raises(ValueError):
        promote_accepted_bridge(audit.bridges[0], veto.verdict)


# ---------------------------------------------------------------------------
# Original claim upgrade
# ---------------------------------------------------------------------------


def test_original_claim_upgrades_from_bridge_required() -> None:
    audit, res = _audit_and_consilium()
    original = Claim(
        content="the street is wet",
        method="logical_audit",
        state=ClaimState.BRIDGE_REQUIRED,
        provenance=Provenance(source="logical_audit", run_id="r1"),
    )
    upgraded = upgrade_original_claim(
        original,
        accepted_bridge_state=BridgeState.CONSILIUM_ACCEPTED,
        verdict=res.verdict.verdict,
    )
    assert upgraded.state is ClaimState.LOGICALLY_SUPPORTED
    assert upgraded.content == original.content
    assert upgraded.method == original.method


def test_upgrade_refuses_when_original_is_not_bridge_required() -> None:
    original = Claim(
        content="x", method="m", state=ClaimState.PROPOSED,
        provenance=Provenance(source="s", run_id="r"),
    )
    with pytest.raises(ClaimUpgradeError):
        upgrade_original_claim(
            original,
            accepted_bridge_state=BridgeState.CONSILIUM_ACCEPTED,
            verdict=Verdict.ACCEPT_AS_BRIDGE,
        )


def test_upgrade_refuses_when_bridge_not_accepted() -> None:
    original = Claim(
        content="x", method="m", state=ClaimState.BRIDGE_REQUIRED,
        provenance=Provenance(source="s", run_id="r"),
    )
    with pytest.raises(ClaimUpgradeError):
        upgrade_original_claim(
            original,
            accepted_bridge_state=BridgeState.CONSILIUM_BLOCKED,
            verdict=Verdict.VETO,
        )


def test_upgrade_refuses_when_verdict_not_accept() -> None:
    original = Claim(
        content="x", method="m", state=ClaimState.BRIDGE_REQUIRED,
        provenance=Provenance(source="s", run_id="r"),
    )
    with pytest.raises(ClaimUpgradeError):
        upgrade_original_claim(
            original,
            accepted_bridge_state=BridgeState.CONSILIUM_ACCEPTED,
            verdict=Verdict.NEEDS_MORE_PREMISES,
        )


# ---------------------------------------------------------------------------
# Bridge state lifecycle
# ---------------------------------------------------------------------------


def test_accept_maps_to_consilium_accepted() -> None:
    audit, res = _audit_and_consilium()
    assert res.bridge_state is BridgeState.CONSILIUM_ACCEPTED


def test_veto_maps_to_consilium_blocked() -> None:
    audit = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    res = BridgeConsilium().deliberate(
        audit.bridges[0],
        source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
    )
    assert res.bridge_state is BridgeState.CONSILIUM_BLOCKED
    assert res.verdict.verdict is Verdict.VETO


def test_needs_more_premises_maps_to_consilium_blocked() -> None:
    """v1.6 strengthening: auto-generated bridges for the metaphor
    case are GENERIC_FALLBACK and now hard-VETOed (a strict subset
    of CONSILIUM_BLOCKED). To exercise the NEEDS_MORE_PREMISES →
    CONSILIUM_BLOCKED mapping under v1.6, we hand-construct a
    SPECIFIC bridge so only the DOMAIN_EXAMINER's metaphor flag
    survives."""
    from desi.logic.bridge_claims import (
        BRIDGE_METHOD, BridgeClaim, BridgeKind,
    )
    from desi.memory.claim import Claim, ClaimState, Provenance
    text = "The market is hot. Therefore the city is flooded."
    specific_bridge = BridgeClaim(
        bridge_id="br_market_hot_specific",
        text="market heat causes the city flood",
        claim=Claim(
            content="market heat causes the city flood",
            method=BRIDGE_METHOD,
            state=ClaimState.PROPOSED,
            provenance=Provenance(source="test", run_id="r1"),
        ),
        rationale="hand-crafted specific bridge for metaphor test",
        kind=BridgeKind.SPECIFIC,
    )
    res = BridgeConsilium().deliberate(
        specific_bridge,
        source_claim_id="ac_test",
        original_text=text,
        context="financial_newspaper",
    )
    assert res.bridge_state is BridgeState.CONSILIUM_BLOCKED
    assert res.verdict.verdict is Verdict.NEEDS_MORE_PREMISES


def test_hard_reject_maps_to_consilium_rejected() -> None:
    """Missing source_claim_id → REJECT_BRIDGE → CONSILIUM_REJECTED."""
    audit = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    res = BridgeConsilium().deliberate(
        audit.bridges[0],
        source_claim_id="",  # forced empty
        original_text=audit.text,
    )
    assert res.bridge_state is BridgeState.CONSILIUM_REJECTED
    assert res.verdict.verdict is Verdict.REJECT_BRIDGE
