"""Aufgabe 4 — append-only ledger for the v3.13 routing integrator.

Four closed events — exactly the ones the directive enumerates.
The v3.11 ``FrameTensionLedger`` is **not** touched; this is a
parallel append-only log that records the *routing* decision
made on top of the v3.11 gate verdict.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FrameRoutingLedgerEvent(str, Enum):
    """Closed routing event taxonomy."""

    FRAME_ROUTING_ALLOWED         = "frame_routing_allowed"
    FRAME_ROUTING_INNER_ONLY      = "frame_routing_inner_only"
    FRAME_ROUTING_BLOCKED         = "frame_routing_blocked"
    FRAME_ROUTING_MARKER_REQUIRED = "frame_routing_marker_required"


def _payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class FrameRoutingLedgerEntry:
    event_id: str
    event: FrameRoutingLedgerEvent
    claim_id: str
    inner_frame: str | None
    outer_frame: str | None
    consistency: str
    routed_pipeline: str | None
    payload_hash: str
    recorded_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event": self.event.value,
            "claim_id": self.claim_id,
            "inner_frame": self.inner_frame,
            "outer_frame": self.outer_frame,
            "consistency": self.consistency,
            "routed_pipeline": self.routed_pipeline,
            "payload_hash": self.payload_hash,
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class FrameRoutingLedger:
    entries: list[FrameRoutingLedgerEntry] = field(default_factory=list)

    def append(
        self,
        *,
        event: FrameRoutingLedgerEvent,
        claim_id: str,
        inner_frame: str | None,
        outer_frame: str | None,
        consistency: str,
        routed_pipeline: str | None,
        recorded_at: datetime,
    ) -> FrameRoutingLedgerEntry:
        payload = {
            "event": event.value,
            "claim_id": claim_id,
            "inner_frame": inner_frame,
            "outer_frame": outer_frame,
            "consistency": consistency,
            "routed_pipeline": routed_pipeline,
            "sequence": len(self.entries),
        }
        entry = FrameRoutingLedgerEntry(
            event_id=f"frl_{len(self.entries):06d}",
            event=event,
            claim_id=claim_id,
            inner_frame=inner_frame,
            outer_frame=outer_frame,
            consistency=consistency,
            routed_pipeline=routed_pipeline,
            payload_hash=_payload_hash(payload),
            recorded_at=recorded_at,
        )
        self.entries.append(entry)
        return entry

    def to_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.entries]


__all__ = [
    "FrameRoutingLedger",
    "FrameRoutingLedgerEntry",
    "FrameRoutingLedgerEvent",
]
