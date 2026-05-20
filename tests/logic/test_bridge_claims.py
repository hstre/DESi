"""Tests for v1.2 bridge-claim generation — INV-L5: never auto-promote."""
from __future__ import annotations

import pytest

from desi.memory.claim import ClaimState
from desi.logic import (
    BRIDGE_METHOD,
    BridgeClaim,
    LogicalAuditor,
    LogicalState,
    PremiseExtractor,
    detect_gap,
    propose_bridge,
)


def _ext() -> PremiseExtractor:
    return PremiseExtractor()


# ---------------------------------------------------------------------------
# Bridge generated for the directive's P3 case
# ---------------------------------------------------------------------------


def test_p3_bridge_is_the_street_is_exposed_to_the_rain() -> None:
    props = _ext().extract("It is raining. Therefore the street is wet.")
    gap = detect_gap(props)
    bridge = propose_bridge(props, gap)
    assert bridge is not None
    assert bridge.text == "the street is exposed to the rain"


# ---------------------------------------------------------------------------
# INV-L5: bridge claims never auto-promote
# ---------------------------------------------------------------------------


def test_bridge_claim_state_is_proposed() -> None:
    props = _ext().extract("It is raining. Therefore the street is wet.")
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge.claim.state == ClaimState.PROPOSED


def test_bridge_claim_method_is_logical_bridge() -> None:
    props = _ext().extract("It is raining. Therefore the street is wet.")
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge.claim.method == BRIDGE_METHOD == "logical_bridge"


def test_bridge_claim_does_not_carry_logical_audit_state() -> None:
    """The bridge is a fresh PROPOSED claim, not a verdict."""
    props = _ext().extract("It is raining. Therefore the street is wet.")
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge.claim.state != ClaimState.LOGICALLY_SUPPORTED
    assert bridge.claim.state != ClaimState.LOGICALLY_REJECTED


# ---------------------------------------------------------------------------
# Auditor wires bridge into BRIDGE_REQUIRED result
# ---------------------------------------------------------------------------


def test_auditor_returns_bridge_required_with_bridge_attached() -> None:
    r = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    assert r.state == LogicalState.BRIDGE_REQUIRED
    assert len(r.bridges) == 1
    assert r.bridges[0].text == "the street is exposed to the rain"
    assert r.bridges[0].claim.state == ClaimState.PROPOSED


def test_auditor_state_is_not_supported_when_only_a_bridge_is_proposed() -> None:
    r = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    assert r.state != LogicalState.LOGICALLY_SUPPORTED


# ---------------------------------------------------------------------------
# Bridge id is deterministic
# ---------------------------------------------------------------------------


def test_same_text_produces_same_bridge_id() -> None:
    props = _ext().extract("It is raining. Therefore the street is wet.")
    a = propose_bridge(props, detect_gap(props))
    b = propose_bridge(props, detect_gap(props))
    assert a.bridge_id == b.bridge_id


# ---------------------------------------------------------------------------
# Bridges are not generated for non-bridge gap kinds
# ---------------------------------------------------------------------------


def test_authority_gap_does_not_yield_a_bridge() -> None:
    props = _ext().extract("Professor X says quantum gravity is solved.")
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge is None


def test_unreachable_gap_does_not_yield_a_bridge() -> None:
    props = _ext().extract("a -> b. b -> c. Therefore a -> d.")
    bridge = propose_bridge(props, detect_gap(props))
    assert bridge is None


# ---------------------------------------------------------------------------
# Bridge claim shape
# ---------------------------------------------------------------------------


def test_bridge_to_dict_includes_state_and_method() -> None:
    props = _ext().extract("It is raining. Therefore the street is wet.")
    d = propose_bridge(props, detect_gap(props)).to_dict()
    for k in ("bridge_id", "text", "rationale",
              "claim_state", "claim_method"):
        assert k in d
    assert d["claim_state"] == "proposed"
    assert d["claim_method"] == "logical_bridge"
