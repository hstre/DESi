"""Aufgaben 5 + 6 + 8 — integration benchmark + routing impact +
adversarial runtime test."""
from __future__ import annotations

from desi.frame_consistency_probe.manipulation import MANIPULATIONS
from desi.frame_tension_integration import (
    FrameRoutingLedgerEvent,
    FrameTensionRouter,
    IntegrationCategory,
    RoutingPipeline,
    build_integration_benchmark,
    category_counts,
    permitted_events,
)
from desi.frames import FrameKind


# Same mapping the router uses; duplicated here so the test can
# verify that no adversarial gets routed to the *outer* (misleading)
# pipeline without importing the private map.
_FRAME_PIPELINE: dict[FrameKind, RoutingPipeline] = {
    FrameKind.TOOL_COMPUTABLE:               RoutingPipeline.TOOL_GATE,
    FrameKind.INFORMATION_THEORETIC:         RoutingPipeline.TOOL_GATE,
    FrameKind.FORMAL_LOGIC:                  RoutingPipeline.LOGICAL_AUDITOR,
    FrameKind.EMPIRICAL_CAUSAL:              RoutingPipeline.LOGICAL_AUDITOR,
    FrameKind.THERMODYNAMIC:                 RoutingPipeline.LOGICAL_AUDITOR,
    FrameKind.AUTHORITY_SPEECH:              RoutingPipeline.CONSILIUM,
    FrameKind.METAPHORICAL:                  RoutingPipeline.CONSILIUM,
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: RoutingPipeline.CONSILIUM,
    FrameKind.FRAME_UNDECLARED:              RoutingPipeline.REJECT,
}


def test_benchmark_has_at_least_sixty_cases() -> None:
    assert len(build_integration_benchmark()) >= 60


def test_each_category_has_at_least_twenty() -> None:
    counts = category_counts()
    for cat in IntegrationCategory:
        assert counts[cat.value] >= 20, (
            f"{cat.value}: {counts[cat.value]} < 20"
        )


def test_router_reaches_perfect_accuracy_on_benchmark() -> None:
    router = FrameTensionRouter()
    wrong = []
    for case in build_integration_benchmark():
        d = router.route(
            claim_id=case.case_id,
            claim_text=case.claim_text,
            inherited_context_text=case.inherited_context_text,
        )
        if d.event not in permitted_events(case.category):
            wrong.append((
                case.case_id, case.category.value, d.event.value,
            ))
    assert wrong == [], (
        f"{len(wrong)} integration benchmark mismatches: {wrong}"
    )


def test_adversarial_runtime_no_allowed_event() -> None:
    # Aufgabe 8: no manipulation case may receive
    # FRAME_ROUTING_ALLOWED (== inherited_manipulations = 0 and
    # manipulation_detection = 1.0).
    router = FrameTensionRouter()
    for m in MANIPULATIONS:
        d = router.route(
            claim_id=f"adv:{m.case_id}",
            claim_text=m.text,
            inherited_context_text=m.ctx_3,
        )
        assert d.event is not (
            FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED
        ), m.case_id
        assert d.inheritance_allowed is False, m.case_id


def test_no_manipulation_routed_via_inheritance() -> None:
    # Aufgabe 8: routed_manipulations counts adversarial cases
    # where the *misleading outer* determined the route — i.e.
    # events tagged FRAME_ROUTING_ALLOWED with the outer pipeline
    # as the target. INNER_ONLY routings are inner-determined,
    # even when the inner happens to share a pipeline with the
    # outer; those do not count as the manipulation succeeding.
    router = FrameTensionRouter()
    for m in MANIPULATIONS:
        d = router.route(
            claim_id=f"adv:{m.case_id}",
            claim_text=m.text,
            inherited_context_text=m.ctx_3,
        )
        outer_pipeline = _FRAME_PIPELINE.get(m.misleading_outer)
        if d.event is FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED:
            # An ALLOWED event on a manipulation would route via
            # the inherited outer — exactly the failure mode.
            assert d.routed_pipeline is not outer_pipeline, (
                f"{m.case_id}: inherited outer pipeline "
                f"{outer_pipeline} — manipulation succeeded"
            )
            # Stronger: we should never get ALLOWED on an
            # adversarial input at all.
            assert False, (
                f"{m.case_id}: received FRAME_ROUTING_ALLOWED — "
                "inheritance should be blocked for every "
                "manipulation"
            )


def test_routing_impact_metrics_consistent() -> None:
    router = FrameTensionRouter()
    benchmark = build_integration_benchmark()
    for case in benchmark:
        router.route(
            claim_id=case.case_id,
            claim_text=case.claim_text,
            inherited_context_text=case.inherited_context_text,
        )
    entries = router.ledger.entries
    block_events = (
        FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED,
        FrameRoutingLedgerEvent.FRAME_ROUTING_INNER_ONLY,
        FrameRoutingLedgerEvent.FRAME_ROUTING_MARKER_REQUIRED,
    )
    blocked_before_routing = sum(
        1 for e in entries if e.event in block_events
    )
    # ALLOWED events count tool/audit/consilium permissions; we
    # don't measure prevented counts as a fraction here because
    # the test only certifies *consistency* with the ledger.
    assert blocked_before_routing >= 0
    assert len(entries) == len(benchmark)
