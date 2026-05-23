"""Tests for v1.3 INV-C3 — a single unresolved veto blocks acceptance."""
from __future__ import annotations

from desi.consilium import (
    BridgeConsilium,
    BridgeState,
    ConsiliumRole,
    Verdict,
)
from desi.logic import LogicalAuditor


def _rain_bridge():
    r = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    return r.bridges[0], r


# ---------------------------------------------------------------------------
# Clean bridge — all four pass
# ---------------------------------------------------------------------------


def test_clean_bridge_is_accepted() -> None:
    bridge, audit = _rain_bridge()
    res = BridgeConsilium().deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
    )
    assert res.verdict.verdict is Verdict.ACCEPT_AS_BRIDGE
    assert res.bridge_state is BridgeState.CONSILIUM_ACCEPTED
    assert res.verdict.blocking_roles == ()


# ---------------------------------------------------------------------------
# One counterexample triggers VETO
# ---------------------------------------------------------------------------


def test_single_counterexample_triggers_veto() -> None:
    bridge, audit = _rain_bridge()
    res = BridgeConsilium().deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
    )
    assert res.verdict.verdict is Verdict.VETO
    assert res.bridge_state is BridgeState.CONSILIUM_BLOCKED
    assert ConsiliumRole.SKEPTIC in res.verdict.blocking_roles


def test_veto_carries_a_rationale() -> None:
    bridge, audit = _rain_bridge()
    res = BridgeConsilium().deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
    )
    assert "counterexample" in res.verdict.rationale.lower()


# ---------------------------------------------------------------------------
# INV-C3: VETO overrides any "needs_more_premises" signal
# ---------------------------------------------------------------------------


def test_veto_overrides_needs_more_premises() -> None:
    """If both SKEPTIC vetos AND DOMAIN_EXAMINER asks for more
    premises, the verdict is VETO (the harder block)."""
    bridge, audit = _rain_bridge()
    res = BridgeConsilium().deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text,
        additional_conditions=("the street has a roof",),
        context="financial_newspaper",
    )
    assert res.verdict.verdict is Verdict.VETO


# ---------------------------------------------------------------------------
# Multiple vetoing roles all appear in blocking_roles
# ---------------------------------------------------------------------------


def test_multiple_vetoing_roles_are_recorded() -> None:
    """Empty bridge text fails LOGICIAN + INTEGRATOR simultaneously."""
    from desi.logic.bridge_claims import BridgeClaim, BRIDGE_METHOD
    from desi.memory.claim import Claim, ClaimState, Provenance
    bridge = BridgeClaim(
        bridge_id="br_empty",
        text="   ",
        claim=Claim(
            content="placeholder",
            method=BRIDGE_METHOD,
            state=ClaimState.PROPOSED,
            provenance=Provenance(source="x", run_id="r1"),
        ),
        rationale="bridge needs empty text for this stress test",
    )
    res = BridgeConsilium().deliberate(
        bridge, source_claim_id="ac_x",
        original_text="It is raining. Therefore the street is wet.",
    )
    # Empty/whitespace-only bridge text is rejected at the input
    # contract before role reviews run.
    assert res.verdict.verdict is Verdict.REJECT_BRIDGE
    assert res.bridge_state is BridgeState.CONSILIUM_REJECTED


# ---------------------------------------------------------------------------
# Bridge that fails ONLY the integrator vetos
# ---------------------------------------------------------------------------


def test_off_topic_bridge_vetos() -> None:
    """A bridge that mentions neither premise nor conclusion's
    subject fails the LOGICIAN and the INTEGRATOR."""
    from desi.logic.bridge_claims import BridgeClaim, BRIDGE_METHOD
    from desi.memory.claim import Claim, ClaimState, Provenance
    bridge = BridgeClaim(
        bridge_id="br_offtopic",
        text="kangaroos navigate by stars at dusk",
        claim=Claim(
            content="kangaroos navigate by stars at dusk",
            method=BRIDGE_METHOD,
            state=ClaimState.PROPOSED,
            provenance=Provenance(source="x", run_id="r1"),
        ),
        rationale="off-topic bridge for stress test",
    )
    res = BridgeConsilium().deliberate(
        bridge, source_claim_id="ac_x",
        original_text="It is raining. Therefore the street is wet.",
    )
    assert res.verdict.verdict is Verdict.VETO
    assert ConsiliumRole.LOGICIAN in res.verdict.blocking_roles
    assert ConsiliumRole.INTEGRATOR in res.verdict.blocking_roles
