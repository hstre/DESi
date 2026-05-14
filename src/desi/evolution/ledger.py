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
    """The v0.6 + v0.7 ledger event taxonomy."""

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
    # v0.7: behaviour-effective config activation + stable-vs-clone
    # metrics + per-mutation cycle summary.
    CONFIG_ACTIVATED = "config_activated"
    METRICS_DELTA = "metrics_delta"
    EVOLUTION_CYCLE = "evolution_cycle"
    # v0.8: multi-seed evaluation + significance gating. The trio is
    # always written in this order: STARTED at the top of an N-seed
    # cycle, one RESULT per scenario after aggregation, and exactly
    # one DECISION after the SignificanceGate runs.
    MULTI_SEED_STARTED = "multi_seed_started"
    MULTI_SEED_RESULT = "multi_seed_result"
    SIGNIFICANCE_DECISION = "significance_decision"
    # v0.9: per-(scenario, seed) audit record. Written once per
    # individual seed run, in addition to the v0.8 per-scenario
    # aggregate. Carries scenario_id, seed, permutation_id, verdict,
    # and metrics so a later audit can reconstruct the path each seed
    # actually took.
    SEED_RUN_RESULT = "seed_run_result"
    # v1.0: natural-language entry point. Written by SPLAdapter to
    # document every text → Claim projection. The three events form
    # a strict order: STARTED on entry, one CANDIDATE_EMITTED per
    # backend output, REJECTED for every gateway block (and every
    # backend / cost-guard failure).
    SEMANTIC_PROJECTION_STARTED = "semantic_projection_started"
    SEMANTIC_CANDIDATE_EMITTED = "semantic_candidate_emitted"
    SEMANTIC_PROJECTION_REJECTED = "semantic_projection_rejected"


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
    "EvolutionLedgerJSONL",
    "LedgerEntry",
    "LedgerEventType",
]


# ---------------------------------------------------------------------------
# v0.7: JSONL file-backed append-only ledger
# ---------------------------------------------------------------------------


class EvolutionLedgerJSONL(EvolutionLedger):
    """Append-only file-backed ledger persisting to ``ledger.jsonl``.

    One JSON object per line. The file is opened in append mode and
    never seek-rewinds: a process restart that has the same file is
    transparent because the on-disk format is line-additive. Reading
    the persisted ledger back uses :meth:`load_from_disk`, which
    reconstructs in-memory :class:`LedgerEntry` records without ever
    modifying the file.

    Properties:

    * deterministic — same payload → same line bytes (canonical JSON,
      sorted keys, no whitespace)
    * diffable — one event per line
    * git-versionable — append-only at the disk level mirrors the
      in-memory invariant
    * forensic — entries written are never removed by this class
    """

    import pathlib  # noqa: PLC0415 — local import to avoid module-level cost

    def __init__(
        self,
        path,  # type: pathlib.Path | str
        *,
        version: str = "v0.7",
    ) -> None:
        import pathlib as _pl
        super().__init__(version=version)
        self._path: _pl.Path = _pl.Path(path)
        if self._path.exists():
            # Replay existing on-disk entries into memory without
            # touching the file.
            for line in self._path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                ts = rec["timestamp"]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                self._entries.append(LedgerEntry(
                    ledger_id=rec["ledger_id"],
                    event_type=LedgerEventType(rec["event_type"]),
                    timestamp=ts,
                    parent_event_id=rec.get("parent_event_id"),
                    payload_hash=rec["payload_hash"],
                    payload=dict(rec["payload"]),
                    actor=rec["actor"],
                    version=rec["version"],
                ))
        else:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self):
        return self._path

    def append(
        self,
        event_type: LedgerEventType,
        payload: dict[str, Any],
        *,
        actor: str = "desi.evolution",
        parent_event_id: str | None = None,
    ) -> LedgerEntry:
        entry = super().append(
            event_type, payload, actor=actor,
            parent_event_id=parent_event_id,
        )
        # Persist this entry as one JSON line. Canonical encoding so
        # the bytes are deterministic for two ledgers given the same
        # payload + ledger_id + timestamp.
        line = json.dumps(
            entry.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            default=_default,
        )
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return entry
