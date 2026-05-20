"""Tests for v1.3 INV-C1 — role-order permutation invariance.

C5 scenario: all 24 permutations of the four roles must produce
identical verdicts AND identical replay hashes.
"""
from __future__ import annotations

from itertools import permutations

import pytest

from desi.consilium import (
    BridgeConsilium,
    CANONICAL_ROLE_ORDER,
    ConsiliumRole,
    Verdict,
)
from desi.logic import LogicalAuditor


@pytest.fixture
def rain_bridge():
    aud = LogicalAuditor().audit(
        "It is raining. Therefore the street is wet."
    )
    return aud.bridges[0], aud


# ---------------------------------------------------------------------------
# All 24 permutations on a clean bridge — identical verdict
# ---------------------------------------------------------------------------


def test_all_24_permutations_yield_identical_verdict(rain_bridge) -> None:
    bridge, audit = rain_bridge
    cons = BridgeConsilium()
    verdicts = set()
    for perm in permutations(CANONICAL_ROLE_ORDER):
        res = cons.deliberate(
            bridge, source_claim_id=audit.audit_id,
            original_text=audit.text, role_order=perm,
        )
        verdicts.add(res.verdict.verdict)
    assert len(verdicts) == 1
    assert verdicts == {Verdict.ACCEPT_AS_BRIDGE}


def test_all_24_permutations_yield_identical_replay_hash(rain_bridge) -> None:
    bridge, audit = rain_bridge
    cons = BridgeConsilium()
    hashes = set()
    for perm in permutations(CANONICAL_ROLE_ORDER):
        res = cons.deliberate(
            bridge, source_claim_id=audit.audit_id,
            original_text=audit.text, role_order=perm,
        )
        hashes.add(res.replay_hash)
    assert len(hashes) == 1


def test_role_order_does_not_change_blocking_role_set(rain_bridge) -> None:
    """When a veto fires, the SET of blocking roles is order-invariant."""
    bridge, audit = rain_bridge
    cons = BridgeConsilium()
    role_sets = set()
    for perm in permutations(CANONICAL_ROLE_ORDER):
        res = cons.deliberate(
            bridge, source_claim_id=audit.audit_id,
            original_text=audit.text,
            additional_conditions=("the street has a roof",),
            role_order=perm,
        )
        role_sets.add(frozenset(res.verdict.blocking_roles))
    assert len(role_sets) == 1


# ---------------------------------------------------------------------------
# Role-order is recorded faithfully in the result (cosmetic, not semantic)
# ---------------------------------------------------------------------------


def test_role_order_is_recorded_on_result(rain_bridge) -> None:
    bridge, audit = rain_bridge
    cons = BridgeConsilium()
    requested = (ConsiliumRole.INTEGRATOR, ConsiliumRole.SKEPTIC,
                 ConsiliumRole.DOMAIN_EXAMINER, ConsiliumRole.LOGICIAN)
    res = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text, role_order=requested,
    )
    assert res.role_order == requested


def test_reviews_are_returned_in_role_order(rain_bridge) -> None:
    bridge, audit = rain_bridge
    cons = BridgeConsilium()
    requested = (ConsiliumRole.INTEGRATOR, ConsiliumRole.SKEPTIC,
                 ConsiliumRole.DOMAIN_EXAMINER, ConsiliumRole.LOGICIAN)
    res = cons.deliberate(
        bridge, source_claim_id=audit.audit_id,
        original_text=audit.text, role_order=requested,
    )
    assert tuple(r.role for r in res.reviews) == requested
