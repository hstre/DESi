"""Tests for v1.4 RecursiveResolver — R1 (single bridge) + R2 (chain)."""
from __future__ import annotations

from desi.recursive import (
    RecursiveResolutionResult,
    RecursiveResolver,
    ResolutionState,
)

from ._helpers import (
    ScriptedAuditor,
    ScriptedConsilium,
    gap,
    needs_bridge,
    supported,
)


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


def test_resolve_returns_recursive_resolution_result() -> None:
    r = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    assert isinstance(r, RecursiveResolutionResult)


def test_result_carries_required_fields() -> None:
    r = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    for f in ("root_claim_id", "resolved_claims", "open_gaps",
              "blocked_claims", "depth_reached", "replay_hash",
              "final_state"):
        assert hasattr(r, f), f"missing field: {f}"


# ---------------------------------------------------------------------------
# R1: single bridge with the real components → COMPLETE at depth 1
# ---------------------------------------------------------------------------


def test_r1_single_bridge_resolves_complete() -> None:
    r = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.depth_reached == 1
    assert r.blocked_claims == ()
    assert r.open_gaps == ()
    assert len(r.resolved_claims) >= 2  # root + bridge leaf


def test_r1_replay_hash_is_non_empty() -> None:
    r = RecursiveResolver().resolve(
        "It is raining. Therefore the street is wet."
    )
    assert r.replay_hash.startswith("rr_")
    assert len(r.replay_hash) == 19


# ---------------------------------------------------------------------------
# R2: scripted two-bridge chain → COMPLETE at depth 2
# ---------------------------------------------------------------------------


def test_r2_two_bridge_chain_resolves_complete() -> None:
    auditor = ScriptedAuditor(script={
        "root":  needs_bridge("root", "bridge_b1"),
        "bridge_b1": needs_bridge("bridge_b1", "bridge_b2"),
        "bridge_b2": gap("bridge_b2"),  # leaf, accepted by parent consilium
    })
    consilium = ScriptedConsilium()  # default ACCEPT_AS_BRIDGE
    r = RecursiveResolver(
        auditor=auditor, consilium=consilium,
    ).resolve("root")
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.depth_reached == 2
    assert len(r.resolved_claims) == 3  # root + b1 + b2


# ---------------------------------------------------------------------------
# Root-level LOGICALLY_SUPPORTED short-circuit (no bridges)
# ---------------------------------------------------------------------------


def test_root_already_supported_resolves_immediately() -> None:
    auditor = ScriptedAuditor(script={"x": supported("x")})
    r = RecursiveResolver(
        auditor=auditor, consilium=ScriptedConsilium(),
    ).resolve("x")
    assert r.final_state is ResolutionState.RESOLUTION_COMPLETE
    assert r.depth_reached == 0


# ---------------------------------------------------------------------------
# Root has no chain → BLOCKED
# ---------------------------------------------------------------------------


def test_root_with_no_explicit_chain_is_blocked() -> None:
    r = RecursiveResolver().resolve("Water boils at 100C.")
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.depth_reached == 0
    assert len(r.blocked_claims) == 1
