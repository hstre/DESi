"""RulePatchRecord — Aufgabe 2.

The deterministic artefact produced by the protocol. ``replay_hash``
is computed over every field except the timestamp (which is
explicitly excluded so two protocol runs on identical inputs yield
identical hashes).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .phases import PatchPhase


@dataclass(frozen=True)
class PhaseOutcome:
    """One phase's verdict + free-form data payload."""

    phase: PatchPhase
    passed: bool
    reason: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "passed": self.passed,
            "reason": self.reason,
            "data": self.data,
        }


@dataclass(frozen=True)
class RulePatchRecord:
    """The eleven required fields of a v2.8 patch record."""

    patch_id: str
    target_rule: str
    source_branch: str
    phase: PatchPhase
    passed: bool
    created_guards: tuple[str, ...]
    touched_files: tuple[str, ...]
    benchmark_hash_before: str
    benchmark_hash_after: str
    replay_hash: str
    timestamp: datetime
    phase_outcomes: tuple[PhaseOutcome, ...] = field(default_factory=tuple)
    fail_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "target_rule": self.target_rule,
            "source_branch": self.source_branch,
            "phase": self.phase.value,
            "passed": self.passed,
            "created_guards": list(self.created_guards),
            "touched_files": list(self.touched_files),
            "benchmark_hash_before": self.benchmark_hash_before,
            "benchmark_hash_after": self.benchmark_hash_after,
            "replay_hash": self.replay_hash,
            "timestamp": self.timestamp.isoformat(),
            "phase_outcomes": [o.to_dict() for o in self.phase_outcomes],
            "fail_reason": self.fail_reason,
        }


def compute_record_replay_hash(payload: dict[str, Any]) -> str:
    """Deterministic 16-hex hash over a record payload.

    ``timestamp`` and ``replay_hash`` are excluded so the hash is
    invariant under wall-clock differences.
    """
    cleaned = {k: v for k, v in payload.items()
               if k not in ("timestamp", "replay_hash")}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


__all__ = [
    "PhaseOutcome",
    "RulePatchRecord",
    "compute_record_replay_hash",
]
