"""ShadowLedger — v2.0 sandbox-only audit log.

The directive forbids modifying ``stable-v1.9.0``. The main
:class:`desi.evolution.EvolutionLedger` and its ``LedgerEventType``
enum are part of v1.9.0; we do not extend either. Instead, v2.0
introduces a *parallel* ledger with its own closed event-type enum.

Same canonical-JSON discipline as v0.7+: ``sort_keys=True``,
``separators=(",", ":")``, deterministic ``payload_hash`` over the
canonical encoding, append-only on disk (when persisted) and in
memory.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ShadowLedgerEventType(str, Enum):
    """The eight v2.0 sandbox-only events."""

    SANDBOX_STARTED = "sandbox_started"
    MUTATION_PROPOSED = "mutation_proposed"
    MUTATION_APPLIED = "mutation_applied"
    BENCHMARK_STARTED = "benchmark_started"
    BENCHMARK_COMPLETED = "benchmark_completed"
    MUTATION_ACCEPTED = "mutation_accepted"
    MUTATION_REJECTED = "mutation_rejected"
    SANDBOX_COMPLETED = "sandbox_completed"


def _canonical(payload: Any) -> str:
    """Canonical JSON encoding matching the v0.7 ledger contract."""
    return json.dumps(
        _normalise(payload),
        sort_keys=True, separators=(",", ":"),
        default=_default,
    )


def _normalise(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _normalise(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalise(x) for x in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _default(o: Any) -> Any:
    if isinstance(o, Enum):
        return o.value
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, (set, tuple)):
        return list(o)
    raise TypeError(f"non-serialisable: {type(o).__name__}")


def _payload_hash(payload: dict[str, Any]) -> str:
    raw = _canonical(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class ShadowLedgerEntry:
    """One append-only entry in the shadow ledger."""

    ledger_id: str
    event_type: ShadowLedgerEventType
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


class ShadowLedger:
    """Append-only in-memory ledger with optional JSONL persistence.

    Two append-only properties enforced:

    1. ``append`` never modifies a prior entry.
    2. If a ``path`` is configured, the file is opened in ``"a"``
       mode and never seek-rewinds; re-opening the file replays
       prior entries into memory without touching disk.
    """

    def __init__(
        self,
        *,
        path: pathlib.Path | str | None = None,
    ) -> None:
        self._entries: list[ShadowLedgerEntry] = []
        self._path: pathlib.Path | None = (
            pathlib.Path(path) if path is not None else None
        )
        if self._path is not None and self._path.exists():
            self._replay_from_disk()
        elif self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        event_type: ShadowLedgerEventType,
        payload: dict[str, Any],
    ) -> ShadowLedgerEntry:
        entry = ShadowLedgerEntry(
            ledger_id="sl_" + uuid.uuid4().hex[:12],
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            payload_hash=_payload_hash(payload),
            payload=dict(payload),
        )
        self._entries.append(entry)
        if self._path is not None:
            self._write_line(entry)
        return entry

    def entries(self) -> tuple[ShadowLedgerEntry, ...]:
        return tuple(self._entries)

    def filter(
        self,
        event_type: ShadowLedgerEventType,
    ) -> list[ShadowLedgerEntry]:
        return [e for e in self._entries if e.event_type is event_type]

    def __len__(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _write_line(self, entry: ShadowLedgerEntry) -> None:
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
            self._entries.append(ShadowLedgerEntry(
                ledger_id=rec["ledger_id"],
                event_type=ShadowLedgerEventType(rec["event_type"]),
                timestamp=ts,
                payload_hash=rec["payload_hash"],
                payload=dict(rec["payload"]),
            ))


__all__ = [
    "ShadowLedger",
    "ShadowLedgerEntry",
    "ShadowLedgerEventType",
]
