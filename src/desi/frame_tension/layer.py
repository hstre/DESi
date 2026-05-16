"""Aufgabe 5 — runtime gate that maps a ``ConsistencyVerdict`` to
an allow/block decision plus a ledger event.

Closed mapping (no other outcomes):

* ``CONFIRMED``    → ``inherited_allowed=True``  /
                     ``FRAME_INHERITANCE_ALLOWED``
* ``TENSION``      → ``inherited_allowed=False`` /
                     ``FRAME_INHERITANCE_BLOCKED``
                     (explicit inner frame may still proceed)
* ``CONFLICT``     → ``inherited_allowed=False`` /
                     ``FRAME_CONFLICT_BLOCKED``
                     (fail-closed; no pipeline)
* ``UNDECIDABLE``  → ``inherited_allowed=False`` /
                     ``FRAME_UNDECIDABLE_BLOCKED``
                     (explicit marker required to proceed)

The layer never decides truth. It decides only whether the
inherited outer context may set the downstream pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .consistency import (
    ConsistencyVerdict,
    FrameConsistency,
    evaluate_consistency,
)
from .ledger import (
    FrameTensionLedger,
    FrameTensionLedgerEntry,
    FrameTensionLedgerEvent,
)


_DECISION_MAP: dict[FrameConsistency, tuple[bool, FrameTensionLedgerEvent]] = {
    FrameConsistency.CONFIRMED: (
        True,  FrameTensionLedgerEvent.FRAME_INHERITANCE_ALLOWED,
    ),
    FrameConsistency.TENSION: (
        False, FrameTensionLedgerEvent.FRAME_INHERITANCE_BLOCKED,
    ),
    FrameConsistency.CONFLICT: (
        False, FrameTensionLedgerEvent.FRAME_CONFLICT_BLOCKED,
    ),
    FrameConsistency.UNDECIDABLE: (
        False, FrameTensionLedgerEvent.FRAME_UNDECIDABLE_BLOCKED,
    ),
}


@dataclass(frozen=True)
class LayerDecision:
    claim_id: str
    consistency: FrameConsistency
    inherited_allowed: bool
    event: FrameTensionLedgerEvent
    inner_frame: str | None
    outer_frame: str | None
    ledger_entry_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "consistency": self.consistency.value,
            "inherited_allowed": self.inherited_allowed,
            "event": self.event.value,
            "inner_frame": self.inner_frame,
            "outer_frame": self.outer_frame,
            "ledger_entry_id": self.ledger_entry_id,
        }


class FrameTensionLayer:
    """Stateful gate: holds the ledger across decisions."""

    def __init__(self, ledger: FrameTensionLedger | None = None) -> None:
        self._ledger = ledger if ledger is not None else FrameTensionLedger()

    @property
    def ledger(self) -> FrameTensionLedger:
        return self._ledger

    def gate(
        self,
        *,
        claim_id: str,
        claim_text: str,
        inherited_context_text: str,
        recorded_at: datetime | None = None,
    ) -> LayerDecision:
        verdict = evaluate_consistency(
            claim_id=claim_id,
            claim_text=claim_text,
            inherited_context_text=inherited_context_text,
        )
        return self._decide(verdict=verdict, claim_id=claim_id,
                            recorded_at=recorded_at)

    def gate_from_verdict(
        self,
        *,
        claim_id: str,
        verdict: ConsistencyVerdict,
        recorded_at: datetime | None = None,
    ) -> LayerDecision:
        return self._decide(verdict=verdict, claim_id=claim_id,
                            recorded_at=recorded_at)

    def _decide(
        self,
        *,
        verdict: ConsistencyVerdict,
        claim_id: str,
        recorded_at: datetime | None,
    ) -> LayerDecision:
        allowed, event = _DECISION_MAP[verdict.consistency]
        when = recorded_at if recorded_at is not None else (
            datetime.now(timezone.utc)
        )
        inner = (
            verdict.inner.declared.value if verdict.inner.declared
            else None
        )
        outer = (
            verdict.outer.declared.value if verdict.outer.declared
            else None
        )
        entry: FrameTensionLedgerEntry = self._ledger.append(
            event=event,
            claim_id=claim_id,
            inner_frame=inner,
            outer_frame=outer,
            consistency=verdict.consistency.value,
            recorded_at=when,
        )
        return LayerDecision(
            claim_id=claim_id,
            consistency=verdict.consistency,
            inherited_allowed=allowed,
            event=event,
            inner_frame=inner,
            outer_frame=outer,
            ledger_entry_id=entry.event_id,
        )


__all__ = [
    "FrameTensionLayer",
    "LayerDecision",
]
