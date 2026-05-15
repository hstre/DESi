"""v2.2 depth-sandbox ledger — Aufgabe 7.

A second parallel ledger, sibling to the v2.0 :class:`ShadowLedger`.
The v2.0 ``ShadowLedgerEventType`` is closed and must not be
extended; v2.2 events live in their own closed 6-value enum.

Canonical-JSON discipline, deterministic ``payload_hash``,
append-only on disk and in memory — same contract as v2.0.
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

from .ledger import _canonical, _default, _normalise


class DepthLedgerEventType(str, Enum):
    """The six v2.2 depth-sandbox events (closed)."""

    DEPTH_MUTATION_PROPOSED = "depth_mutation_proposed"
    DEPTH_MUTATION_APPLIED = "depth_mutation_applied"
    DEPTH_STRESS_STARTED = "depth_stress_started"
    DEPTH_STRESS_COMPLETED = "depth_stress_completed"
    DEPTH_MUTATION_ACCEPTED = "depth_mutation_accepted"
    DEPTH_MUTATION_REJECTED = "depth_mutation_rejected"


def _payload_hash(payload: dict[str, Any]) -> str:
    raw = _canonical(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class DepthLedgerEntry:
    ledger_id: str
    event_type: DepthLedgerEventType
    timestamp: datetime
    payload_hash: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "payload_hash": self.payload_hash,
            "payload": _normalise(self.payload),
        }


class DepthShadowLedger:
    """Append-only ledger for the v2.2 depth sandbox."""

    def __init__(self, *, path: pathlib.Path | str | None = None) -> None:
        self._entries: list[DepthLedgerEntry] = []
        self._path: pathlib.Path | None = (
            pathlib.Path(path) if path is not None else None
        )
        if self._path is not None and self._path.exists():
            self._replay_from_disk()
        elif self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        event_type: DepthLedgerEventType,
        payload: dict[str, Any],
    ) -> DepthLedgerEntry:
        entry = DepthLedgerEntry(
            ledger_id="dl_" + uuid.uuid4().hex[:12],
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            payload_hash=_payload_hash(payload),
            payload=dict(payload),
        )
        self._entries.append(entry)
        if self._path is not None:
            self._write_line(entry)
        return entry

    def entries(self) -> tuple[DepthLedgerEntry, ...]:
        return tuple(self._entries)

    def filter(
        self,
        event_type: DepthLedgerEventType,
    ) -> list[DepthLedgerEntry]:
        return [e for e in self._entries if e.event_type is event_type]

    def __len__(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _write_line(self, entry: DepthLedgerEntry) -> None:
        line = json.dumps(
            entry.to_dict(),
            sort_keys=True, separators=(",", ":"),
            default=_default,
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
            self._entries.append(DepthLedgerEntry(
                ledger_id=rec["ledger_id"],
                event_type=DepthLedgerEventType(rec["event_type"]),
                timestamp=ts,
                payload_hash=rec["payload_hash"],
                payload=dict(rec["payload"]),
            ))


__all__ = [
    "DepthLedgerEntry",
    "DepthLedgerEventType",
    "DepthShadowLedger",
]
