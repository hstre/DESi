"""Aufgaben 2 + 3 + 4 — router contract + ledger events."""
from __future__ import annotations

from desi.frame_tension import FrameConsistency
from desi.frame_tension_integration import (
    FrameRoutingLedgerEvent,
    FrameTensionRouter,
    RoutingPipeline,
)


def test_ledger_event_has_four_values() -> None:
    assert len(list(FrameRoutingLedgerEvent)) == 4


def test_ledger_event_values() -> None:
    assert {e.value for e in FrameRoutingLedgerEvent} == {
        "frame_routing_allowed",
        "frame_routing_inner_only",
        "frame_routing_blocked",
        "frame_routing_marker_required",
    }


def test_routing_pipeline_is_closed_four_value_enum() -> None:
    assert len(list(RoutingPipeline)) == 4
    assert {p.value for p in RoutingPipeline} == {
        "tool_gate",
        "logical_auditor",
        "consilium",
        "reject",
    }


def test_confirmed_routes_to_matching_pipeline() -> None:
    r = FrameTensionRouter()
    d = r.route(
        claim_id="c1",
        claim_text="Heat flow in joules per second drives the engine.",
        inherited_context_text="Frame: thermodynamic",
    )
    assert d.consistency is FrameConsistency.CONFIRMED
    assert d.event is FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED
    assert d.inheritance_allowed is True
    assert d.routed_pipeline is RoutingPipeline.LOGICAL_AUDITOR


def test_tension_routes_inner_only_not_outer() -> None:
    r = FrameTensionRouter()
    # Inner = thermo (joules per second), outer = info (Frame).
    # Router must block inheritance and route via inner.
    d = r.route(
        claim_id="c1",
        claim_text="Heat flow in joules per second drives the engine.",
        inherited_context_text="Frame: information-theoretic",
    )
    assert d.consistency is FrameConsistency.TENSION
    assert d.event is FrameRoutingLedgerEvent.FRAME_ROUTING_INNER_ONLY
    assert d.inheritance_allowed is False
    # Routed via inner = thermo → logical auditor.
    assert d.routed_pipeline is RoutingPipeline.LOGICAL_AUDITOR


def test_conflict_fails_closed() -> None:
    r = FrameTensionRouter()
    d = r.route(
        claim_id="c1",
        claim_text="By modus ponens the syllogism is valid.",
        inherited_context_text="Frame: tool computable",
    )
    assert d.consistency is FrameConsistency.CONFLICT
    assert d.event is FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED
    assert d.routed_pipeline is RoutingPipeline.REJECT
    assert d.inheritance_allowed is False


def test_undecidable_requires_marker() -> None:
    r = FrameTensionRouter()
    d = r.route(
        claim_id="c1",
        claim_text="A neutral sentence.",
        inherited_context_text="Another neutral sentence.",
    )
    assert d.consistency is FrameConsistency.UNDECIDABLE
    assert d.event is (
        FrameRoutingLedgerEvent.FRAME_ROUTING_MARKER_REQUIRED
    )
    assert d.routed_pipeline is None
    assert d.inheritance_allowed is False


def test_router_appends_one_ledger_entry_per_route() -> None:
    r = FrameTensionRouter()
    r.route(claim_id="a", claim_text="Calculate 2 + 3.",
            inherited_context_text="Frame: tool computable")
    r.route(claim_id="b", claim_text="By modus ponens.",
            inherited_context_text="Frame: tool computable")
    assert len(r.ledger.entries) == 2
    assert r.ledger.entries[0].event_id == "frl_000000"
    assert r.ledger.entries[1].event_id == "frl_000001"


def test_ledger_payload_hash_deterministic_across_routers() -> None:
    from datetime import datetime, timezone
    when = datetime(2026, 1, 1, tzinfo=timezone.utc)
    r1 = FrameTensionRouter()
    r2 = FrameTensionRouter()
    d1 = r1.route(claim_id="x", claim_text="Calculate 2 + 3.",
                  inherited_context_text="Frame: tool computable",
                  recorded_at=when)
    d2 = r2.route(claim_id="x", claim_text="Calculate 2 + 3.",
                  inherited_context_text="Frame: tool computable",
                  recorded_at=when)
    assert r1.ledger.entries[0].payload_hash == (
        r2.ledger.entries[0].payload_hash
    )
    assert d1.to_dict() == d2.to_dict()
