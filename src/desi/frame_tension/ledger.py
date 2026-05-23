"""Aufgabe 6 — append-only ledger for the FRAME_TENSION_LAYER.

Four closed event types — exactly the ones the directive
enumerates. The v3.4 ``FrameLedger`` is **not** touched; this is
a parallel append-only log keyed on the layer's own event id.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FrameTensionLedgerEvent(str, Enum):
    """Closed event taxonomy — Aufgabe 6."""

    FRAME_INHERITANCE_ALLOWED = "frame_inheritance_allowed"
    FRAME_INHERITANCE_BLOCKED = "frame_inheritance_blocked"
    FRAME_CONFLICT_BLOCKED    = "frame_conflict_blocked"
    FRAME_UNDECIDABLE_BLOCKED = "frame_undecidable_blocked"


def _payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class FrameTensionLedgerEntry:
    event_id: str
    event: FrameTensionLedgerEvent
    claim_id: str
    inner_frame: str | None
    outer_frame: str | None
    consistency: str
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
            "payload_hash": self.payload_hash,
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class FrameTensionLedger:
    entries: list[FrameTensionLedgerEntry] = field(default_factory=list)

    def append(
        self,
        *,
        event: FrameTensionLedgerEvent,
        claim_id: str,
        inner_frame: str | None,
        outer_frame: str | None,
        consistency: str,
        recorded_at: datetime,
    ) -> FrameTensionLedgerEntry:
        payload = {
            "event": event.value,
            "claim_id": claim_id,
            "inner_frame": inner_frame,
            "outer_frame": outer_frame,
            "consistency": consistency,
            "sequence": len(self.entries),
        }
        entry = FrameTensionLedgerEntry(
            event_id=f"ftl_{len(self.entries):06d}",
            event=event,
            claim_id=claim_id,
            inner_frame=inner_frame,
            outer_frame=outer_frame,
            consistency=consistency,
            payload_hash=_payload_hash(payload),
            recorded_at=recorded_at,
        )
        self.entries.append(entry)
        return entry

    def to_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.entries]


__all__ = [
    "FrameTensionLedger",
    "FrameTensionLedgerEntry",
    "FrameTensionLedgerEvent",
]
