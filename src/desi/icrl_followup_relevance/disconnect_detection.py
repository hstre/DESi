"""v23.3 - disconnect detection.

Checks that every central claim visibly connects back to a
base-paper open problem. A claim that names no anchoring
problem is a disconnect - exactly what would make an author
file the follow-up as unrelated. Built on the v23.0 anchoring
layer.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.icrl_followup_revision import claims, unconnected_claims


@dataclass(frozen=True)
class ConnectionNote:
    claim_id: str
    anchors: tuple[str, ...]
    sprint_source: str
    connected: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "anchors": list(self.anchors),
            "sprint_source": self.sprint_source,
            "connected": self.connected,
        }


def connection_notes() -> tuple[ConnectionNote, ...]:
    return tuple(
        ConnectionNote(
            c.claim_id, tuple(c.anchors), c.sprint_source,
            c.is_anchored(),
        )
        for c in claims()
    )


def disconnected_claims() -> tuple[str, ...]:
    return unconnected_claims()


def paper_connection_visibility() -> float:
    """Fraction of central claims that visibly connect to a
    base-paper open problem, in [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    connected = sum(1 for c in rows if c.is_anchored())
    return round(connected / len(rows), 6)


__all__ = [
    "ConnectionNote",
    "connection_notes",
    "disconnected_claims",
    "paper_connection_visibility",
]
