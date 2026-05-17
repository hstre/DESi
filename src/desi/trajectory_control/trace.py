"""v3.27 — trace log.

Every controller decision (v3.26 actions + v3.27
rollback) is recorded in a per-trajectory ``TraceLog``.
The log is deterministic: replaying the controller on
the same trajectory produces an identical trace.

This is the audit trail the v3.27 sprint adds — without
it, the rollback action would be untraceable and the
``replay_stability`` metric would have nothing to check.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TraceEntry:
    trajectory_id: str
    state_index: int
    action: str            # ActionKind / RollbackKind value
                           # or "no_action"
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "state_index": self.state_index,
            "action": self.action,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class TraceLog:
    trajectory_id: str
    entries: tuple[TraceEntry, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "entries": [e.to_dict() for e in self.entries],
        }

    def signature(self) -> tuple[tuple[int, str], ...]:
        """Compact signature for equality checks across
        replays."""
        return tuple(
            (e.state_index, e.action) for e in self.entries
        )


__all__ = ["TraceEntry", "TraceLog"]
