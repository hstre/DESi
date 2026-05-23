"""SelfDiagnosticReport — final v2.1 artifact (Aufgabe 9).

Two runs of the diagnostic over the same source data must produce
identical ``replay_hash`` values. Timestamps are excluded from the
hash payload for the same reason as in v2.0.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .record import DeficitRecord


@dataclass(frozen=True)
class SelfDiagnosticReport:
    started_at: datetime
    finished_at: datetime
    stable_version: str
    stable_hash_before: str
    stable_hash_after: str
    total_deficits: int
    actionable_deficits: int
    non_actionable_deficits: int
    highest_severity: float
    highest_confidence: float
    dead_knobs: tuple[str, ...]
    live_knobs: tuple[str, ...]
    recommended_next_knob: str | None
    blocked_recommendations: tuple[str, ...]
    deficits: tuple[DeficitRecord, ...] = field(default_factory=tuple)
    replay_hash: str = ""
    reflection: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "stable_version": self.stable_version,
            "stable_hash_before": self.stable_hash_before,
            "stable_hash_after": self.stable_hash_after,
            "total_deficits": self.total_deficits,
            "actionable_deficits": self.actionable_deficits,
            "non_actionable_deficits": self.non_actionable_deficits,
            "highest_severity": self.highest_severity,
            "highest_confidence": self.highest_confidence,
            "dead_knobs": list(self.dead_knobs),
            "live_knobs": list(self.live_knobs),
            "recommended_next_knob": self.recommended_next_knob,
            "blocked_recommendations": list(self.blocked_recommendations),
            "deficits": [d.to_dict() for d in self.deficits],
            "replay_hash": self.replay_hash,
            "reflection": self.reflection,
        }


def compute_report_replay_hash(payload: dict[str, Any]) -> str:
    """Deterministic 16-hex hash over the report payload.

    ``started_at``, ``finished_at`` and ``replay_hash`` are excluded
    so the hash is invariant under re-runs at different wall times.
    """
    cleaned = {k: v for k, v in payload.items()
               if k not in ("started_at", "finished_at", "replay_hash")}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


__all__ = ["SelfDiagnosticReport", "compute_report_replay_hash"]
