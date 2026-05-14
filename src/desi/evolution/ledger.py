"""EvolutionLedger — append-only audit trail for DESi's self-improvement loop.

Every action the evolution layer takes is appended to a ledger. Entries
are immutable once written: there is no update path, no delete path,
no in-place mutation. To record a *change* (e.g. a Veto obligation
transitioning from OPEN to PASSED) the caller appends a new entry; the
original entry stays as-is.

Closed enumeration of v0.6 event types. Adding an event type requires
a code change so that downstream promotion-gating sees a stable
taxonomy.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Iterator


class LedgerEventType(str, Enum):
    """The v0.6 ledger event taxonomy."""

    REFLECTION = "reflection"
    PROPOSAL = "proposal"
    CLONE_CREATED = "clone_created"
    EVALUATION = "evaluation"
    JURY_ROUND1 = "jury_round1"
    JURY_ROUND2 = "jury_round2"
    VETO_VALID = "veto_valid"
    VETO_INVALID = "veto_invalid"
    PROMOTION_DECISION = "promotion_decision"
    SNAPSHOT = "snapshot"
    ROLLBACK = "rollback"
    VETO_OBLIGATION = "veto_obligation"
    OBLIGATION_STATUS_CHANGE = "obligation_status_change"


@dataclass(frozen=True)
class LedgerEntry:
    """One append-only ledger record.

    The frozen dataclass plus the lack of any in-place setter in
    :class:`EvolutionLedger` guarantees that an entry's bytes are
    fixed at the moment of append.
    """

    ledger_id: str
    event_type: LedgerEventType
    timestamp: datetime
    parent_event_id: str | None
    payload_hash: str
    payload: dict[str, Any]
    actor: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "parent_event_id": self.parent_event_id,
            "payload_hash": self.payload_hash,
            "payload": _normalise(self.payload),
            "actor": self.actor,
            "version": self.version,
        }


def _payload_hash(payload: dict[str, Any]) -> str:
    """Deterministic sha256 of the payload after canonical JSON encode."""
    normalised = _normalise(payload)
    raw = json.dumps(normalised, sort_keys=True, separators=(",", ":"),
                     default=_default).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _normalise(value: Any) -> Any:
    """Convert non-JSON-native types into JSON-friendly forms.

    Used both for hashing and for export, so that hash and JSON output
    stay aligned bit-for-bit.
    """
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


class EvolutionLedger:
    """Append-only ledger of evolution-layer events.

    Public surface:

    * :meth:`append`  — add a new entry; never modifies prior entries
    * :meth:`entries` — iterate all entries in insertion order
    * :meth:`filter`  — filter by event type
    * :meth:`find_one` — find a single entry by id
    * :meth:`to_json` — deterministic JSON snapshot
    * :meth:`to_markdown` — human-readable audit log
    """

    def __init__(self, *, version: str = "v0.6") -> None:
        self._entries: list[LedgerEntry] = []
        self._version = version

    # ------------------------------------------------------------------
    # Append + read
    # ------------------------------------------------------------------

    def append(
        self,
        event_type: LedgerEventType,
        payload: dict[str, Any],
        *,
        actor: str = "desi.evolution",
        parent_event_id: str | None = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            ledger_id="le_" + uuid.uuid4().hex[:12],
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            parent_event_id=parent_event_id,
            payload_hash=_payload_hash(payload),
            payload=dict(payload),  # shallow copy keeps caller dict isolated
            actor=actor,
            version=self._version,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> tuple[LedgerEntry, ...]:
        # Return a tuple snapshot so callers cannot append via the list
        # reference.
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[LedgerEntry]:
        return iter(self.entries())

    def filter(
        self,
        event_type: LedgerEventType | None = None,
        *,
        parent_event_id: str | None = None,
    ) -> list[LedgerEntry]:
        out: list[LedgerEntry] = []
        for e in self._entries:
            if event_type is not None and e.event_type is not event_type:
                continue
            if (parent_event_id is not None
                    and e.parent_event_id != parent_event_id):
                continue
            out.append(e)
        return out

    def find_one(self, ledger_id: str) -> LedgerEntry | None:
        for e in self._entries:
            if e.ledger_id == ledger_id:
                return e
        return None

    # ------------------------------------------------------------------
    # Append-only protections
    # ------------------------------------------------------------------

    def verify_append_only(
        self, baseline: tuple[LedgerEntry, ...],
    ) -> bool:
        """Return True iff ``baseline`` is a prefix of the current entries.

        Used by promotion tests: take a snapshot of ``ledger.entries()``
        at the start of a workflow, do work, then call this with the
        snapshot. False means a previous entry was modified or removed.
        """
        current = self.entries()
        if len(current) < len(baseline):
            return False
        for prior, now in zip(baseline, current):
            if prior != now:
                return False
        return True

    # ------------------------------------------------------------------
    # Exporters
    # ------------------------------------------------------------------

    def to_json(self, *, indent: int = 2) -> str:
        doc = {
            "version": self._version,
            "entry_count": len(self._entries),
            "entries": [e.to_dict() for e in self._entries],
        }
        return json.dumps(doc, indent=indent, sort_keys=False,
                          default=_default)

    def to_markdown(self) -> str:
        lines: list[str] = []
        lines.append(f"# DESi evolution ledger — {self._version}")
        lines.append("")
        lines.append(f"Entries: **{len(self._entries)}**. Append-only; "
                     f"prior entries are never modified.")
        lines.append("")
        lines.append("| ledger_id | event_type | timestamp | "
                     "parent | payload_hash | actor |")
        lines.append("|---|---|---|---|---|---|")
        for e in self._entries:
            parent = e.parent_event_id or "—"
            lines.append(
                f"| `{e.ledger_id}` | `{e.event_type.value}` | "
                f"{e.timestamp.isoformat()} | `{parent}` | "
                f"`{e.payload_hash}` | `{e.actor}` |"
            )
        lines.append("")
        return "\n".join(lines)


__all__ = [
    "EvolutionLedger",
    "LedgerEntry",
    "LedgerEventType",
]
