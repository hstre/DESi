"""FrameLedger — Aufgabe 7.

Append-only, deterministic, canonical-JSON payload-hash ledger
for the six new closed event types. The ledger is **separate**
from the v0.7 ``EvolutionLedger``, the v2.0 ``ShadowLedger``, and
the v2.2 ``DepthShadowLedger`` — frames have their own audit
trail by design.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class FrameLedgerEventType(str, Enum):
    """Six v3.4 closed frame-pipeline events."""

    FRAME_DECLARATION_STARTED = "frame_declaration_started"
    FRAME_DECLARED = "frame_declared"
    FRAME_UNDECLARED = "frame_undeclared"
    FRAME_CONFLICT_DETECTED = "frame_conflict_detected"
    FRAME_COMPATIBILITY_CHECKED = "frame_compatibility_checked"
    FRAME_PIPELINE_BLOCKED = "frame_pipeline_blocked"


def _canonical(payload: Any) -> str:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str,
    )


def _payload_hash(payload: dict[str, Any]) -> str:
    raw = _canonical(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class FrameLedgerEntry:
    ledger_id: str
    event_type: FrameLedgerEventType
    timestamp: datetime
    payload_hash: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "payload_hash": self.payload_hash,
            "payload": self.payload,
        }


class FrameLedger:
    """Append-only in-memory ledger + optional JSONL persistence."""

    def __init__(
        self,
        *,
        path: pathlib.Path | str | None = None,
    ) -> None:
        self._entries: list[FrameLedgerEntry] = []
        self._path: pathlib.Path | None = (
            pathlib.Path(path) if path is not None else None
        )
        if self._path is not None and self._path.exists():
            self._replay_from_disk()
        elif self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        event_type: FrameLedgerEventType,
        payload: dict[str, Any],
    ) -> FrameLedgerEntry:
        entry = FrameLedgerEntry(
            ledger_id="fl_" + uuid.uuid4().hex[:12],
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            payload_hash=_payload_hash(payload),
            payload=dict(payload),
        )
        self._entries.append(entry)
        if self._path is not None:
            self._write_line(entry)
        return entry

    def entries(self) -> tuple[FrameLedgerEntry, ...]:
        return tuple(self._entries)

    def filter(
        self,
        event_type: FrameLedgerEventType,
    ) -> list[FrameLedgerEntry]:
        return [e for e in self._entries if e.event_type is event_type]

    def __len__(self) -> int:
        return len(self._entries)

    def _write_line(self, entry: FrameLedgerEntry) -> None:
        line = json.dumps(
            entry.to_dict(),
            sort_keys=True, separators=(",", ":"), default=str,
        )
        with self._path.open("a", encoding="utf-8") as fh:  # type: ignore
            fh.write(line + "\n")

    def _replay_from_disk(self) -> None:
        for raw in self._path.read_text().splitlines():  # type: ignore
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            ts = rec["timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            self._entries.append(FrameLedgerEntry(
                ledger_id=rec["ledger_id"],
                event_type=FrameLedgerEventType(rec["event_type"]),
                timestamp=ts,
                payload_hash=rec["payload_hash"],
                payload=dict(rec["payload"]),
            ))


__all__ = ["FrameLedger", "FrameLedgerEntry", "FrameLedgerEventType"]
