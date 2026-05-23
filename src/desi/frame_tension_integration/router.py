"""Aufgaben 2 + 3 + 4 — pipeline-integrated routing governor.

Sits at the v3.12-recommended POST_FRAME_PRE_ROUTING insertion
point:

    SPL → FrameDeclaration → **FrameTensionLayer** → Routing

The router runs the v3.11 ``FrameTensionLayer`` over each claim
and translates the four ``FrameConsistency`` verdicts into
exactly four routing outcomes (closed mapping, hardcoded — no
config knob):

    CONFIRMED   → route to the inferred pipeline (allowed)
    TENSION     → route only via the explicit *inner* frame
                  (inheritance blocked, inner-only)
    CONFLICT    → fail closed (no pipeline)
    UNDECIDABLE → reject until an explicit ``Frame:`` marker
                  is provided

It does **not** mutate ``logic/``, ``recursive/``, ``consilium/``
or ``tools/``. It only emits routing decisions plus a parallel
``FrameRoutingLedger`` event.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from ..frame_tension import (
    FrameConsistency,
    FrameTensionLayer,
)
from ..frames import FrameKind
from .ledger import (
    FrameRoutingLedger,
    FrameRoutingLedgerEntry,
    FrameRoutingLedgerEvent,
)


class RoutingPipeline(str, Enum):
    """Closed set of downstream pipelines the router may target."""

    TOOL_GATE        = "tool_gate"
    LOGICAL_AUDITOR  = "logical_auditor"
    CONSILIUM        = "consilium"
    REJECT           = "reject"


# Frame → pipeline mapping. Deterministic; reflects DESi's existing
# routing convention (we do not modify the live routers — this map
# only labels which pipeline *would* have received the claim).
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


def _pipeline_for(frame_str: str | None) -> RoutingPipeline | None:
    if frame_str is None:
        return None
    try:
        kind = FrameKind(frame_str)
    except ValueError:
        return None
    return _FRAME_PIPELINE.get(kind)


@dataclass(frozen=True)
class RoutingDecision:
    """One routing outcome plus the ledger receipt."""

    claim_id: str
    consistency: FrameConsistency
    inner_frame: str | None
    outer_frame: str | None
    routed_pipeline: RoutingPipeline | None
    inheritance_allowed: bool
    event: FrameRoutingLedgerEvent
    ledger_entry_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "consistency": self.consistency.value,
            "inner_frame": self.inner_frame,
            "outer_frame": self.outer_frame,
            "routed_pipeline": (
                self.routed_pipeline.value
                if self.routed_pipeline else None
            ),
            "inheritance_allowed": self.inheritance_allowed,
            "event": self.event.value,
            "ledger_entry_id": self.ledger_entry_id,
        }


class FrameTensionRouter:
    """Stateful routing governor.

    Owns one ``FrameTensionLayer`` for the inner/outer gate and
    one ``FrameRoutingLedger`` for the routing receipts. The
    routing mapping is hardcoded — no config option, no
    pluggable strategy.
    """

    def __init__(
        self,
        *,
        layer: FrameTensionLayer | None = None,
        ledger: FrameRoutingLedger | None = None,
    ) -> None:
        self._layer = layer if layer is not None else FrameTensionLayer()
        self._ledger = (
            ledger if ledger is not None else FrameRoutingLedger()
        )

    @property
    def layer(self) -> FrameTensionLayer:
        return self._layer

    @property
    def ledger(self) -> FrameRoutingLedger:
        return self._ledger

    def route(
        self,
        *,
        claim_id: str,
        claim_text: str,
        inherited_context_text: str,
        recorded_at: datetime | None = None,
    ) -> RoutingDecision:
        gate = self._layer.gate(
            claim_id=claim_id,
            claim_text=claim_text,
            inherited_context_text=inherited_context_text,
            recorded_at=recorded_at,
        )
        when = recorded_at if recorded_at is not None else (
            datetime.now(timezone.utc)
        )

        cons = gate.consistency
        inner = gate.inner_frame
        outer = gate.outer_frame

        if cons is FrameConsistency.CONFIRMED:
            # Both sides agree → route to the matching pipeline.
            pipeline = _pipeline_for(inner)
            event = FrameRoutingLedgerEvent.FRAME_ROUTING_ALLOWED
            inheritance_allowed = True
        elif cons is FrameConsistency.TENSION:
            # Inherited outer is blocked; if the inner frame is
            # explicit we still route via it, otherwise the
            # router refuses to route.
            pipeline = _pipeline_for(inner)
            event = FrameRoutingLedgerEvent.FRAME_ROUTING_INNER_ONLY
            inheritance_allowed = False
        elif cons is FrameConsistency.CONFLICT:
            # Fail closed — no pipeline at all.
            pipeline = RoutingPipeline.REJECT
            event = FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED
            inheritance_allowed = False
        elif cons is FrameConsistency.UNDECIDABLE:
            # Wait for an explicit Frame: marker.
            pipeline = None
            event = (
                FrameRoutingLedgerEvent.FRAME_ROUTING_MARKER_REQUIRED
            )
            inheritance_allowed = False
        else:
            # Closed enum — every value handled above. Defensive
            # fallback to fail-closed if a future enum extension
            # bypasses the mapping.
            pipeline = RoutingPipeline.REJECT
            event = FrameRoutingLedgerEvent.FRAME_ROUTING_BLOCKED
            inheritance_allowed = False

        entry: FrameRoutingLedgerEntry = self._ledger.append(
            event=event,
            claim_id=claim_id,
            inner_frame=inner,
            outer_frame=outer,
            consistency=cons.value,
            routed_pipeline=(
                pipeline.value if pipeline is not None else None
            ),
            recorded_at=when,
        )
        return RoutingDecision(
            claim_id=claim_id,
            consistency=cons,
            inner_frame=inner,
            outer_frame=outer,
            routed_pipeline=pipeline,
            inheritance_allowed=inheritance_allowed,
            event=event,
            ledger_entry_id=entry.event_id,
        )


__all__ = [
    "FrameTensionRouter",
    "RoutingDecision",
    "RoutingPipeline",
]
