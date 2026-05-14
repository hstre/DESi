"""Final EvolutionReport — Aufgabe 6.

Aggregates 30 step records into a single deterministic artifact:
acceptance counts, the best-scoring clone, convergence /
oscillation / drift heuristics, and a ``replay_hash`` over the
canonical JSON of the report so an independent observer can confirm
the run was bit-for-bit reproducible.

No heuristics are used to *decide* anything — these are
read-only summary statistics over an already-completed run.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StepOutcome(str, Enum):
    """The four possible outcomes for a single sandbox step."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    KILLED = "killed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class StepRecord:
    """One step in the 30-step evolution sequence."""

    step_id: int
    parent_hash: str
    clone_hash: str
    parameter: str
    parent_value: float
    proposed_value: float
    direction: int
    clamped: bool
    outcome: StepOutcome
    precision: float
    recall: float
    false_positives: int
    authority_blocks: int
    tool_precision: float
    hash_mismatches: int
    failure_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "parent_hash": self.parent_hash,
            "clone_hash": self.clone_hash,
            "parameter": self.parameter,
            "parent_value": self.parent_value,
            "proposed_value": self.proposed_value,
            "direction": self.direction,
            "clamped": self.clamped,
            "outcome": self.outcome.value,
            "precision": self.precision,
            "recall": self.recall,
            "false_positives": self.false_positives,
            "authority_blocks": self.authority_blocks,
            "tool_precision": self.tool_precision,
            "hash_mismatches": self.hash_mismatches,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class EvolutionReport:
    """The Abschlussbericht for one sandbox.run().

    Hard invariants:
      * ``total_steps`` matches ``len(steps)``
      * ``stable_hash_before == stable_hash_after`` (Aufgabe 1)
      * ``replay_hash`` is deterministic — two runs of the same
        sandbox produce the identical hex digest.
    """

    started_at: datetime
    finished_at: datetime
    stable_version: str
    stable_hash_before: str
    stable_hash_after: str
    total_steps: int
    accepted_steps: int
    rejected_steps: int
    killed_steps: int
    best_clone_hash: str
    best_parameter_value: float
    final_parameter_value: float
    local_optima_detected: bool
    oscillation_detected: bool
    convergence_detected: bool
    drift_detected: bool
    steps: tuple[StepRecord, ...] = field(default_factory=tuple)
    replay_hash: str = ""
    reflection: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "stable_version": self.stable_version,
            "stable_hash_before": self.stable_hash_before,
            "stable_hash_after": self.stable_hash_after,
            "total_steps": self.total_steps,
            "accepted_steps": self.accepted_steps,
            "rejected_steps": self.rejected_steps,
            "killed_steps": self.killed_steps,
            "best_clone_hash": self.best_clone_hash,
            "best_parameter_value": self.best_parameter_value,
            "final_parameter_value": self.final_parameter_value,
            "local_optima_detected": self.local_optima_detected,
            "oscillation_detected": self.oscillation_detected,
            "convergence_detected": self.convergence_detected,
            "drift_detected": self.drift_detected,
            "steps": [s.to_dict() for s in self.steps],
            "replay_hash": self.replay_hash,
            "reflection": self.reflection,
        }


# ---------------------------------------------------------------------------
# Heuristic-free summary statistics
# ---------------------------------------------------------------------------


def detect_oscillation(values: list[float]) -> bool:
    """Three or more direction reversals in the accepted-value trail.

    Pure structural test — sign-changes in successive deltas.
    """
    if len(values) < 4:
        return False
    deltas = [b - a for a, b in zip(values, values[1:]) if (b - a) != 0.0]
    reversals = sum(
        1 for x, y in zip(deltas, deltas[1:]) if (x > 0) != (y > 0)
    )
    return reversals >= 3


def detect_convergence(values: list[float], window: int = 5) -> bool:
    """No movement over the last ``window`` accepted values."""
    if len(values) < window:
        return False
    tail = values[-window:]
    return max(tail) == min(tail)


def detect_local_optimum(values: list[float]) -> bool:
    """Direction reverses *and* the new direction never beats the peak."""
    if len(values) < 3:
        return False
    peak = max(values)
    peak_idx = values.index(peak)
    return peak_idx != len(values) - 1 and max(values[peak_idx:]) == peak


def detect_drift(values: list[float], threshold: float = 0.10) -> bool:
    """Cumulative absolute movement exceeds ``threshold`` over the run."""
    if len(values) < 2:
        return False
    return abs(values[-1] - values[0]) > threshold


def compute_replay_hash(report_payload: dict[str, Any]) -> str:
    """Deterministic sha256[:16] over the canonical-JSON of the report.

    The ``replay_hash`` field itself is omitted from the hashing
    payload so the hash is well-defined.
    """
    payload = {k: v for k, v in report_payload.items() if k != "replay_hash"}
    # Strip non-deterministic timestamps — they vary between machines
    # even when the run is logically identical.
    payload.pop("started_at", None)
    payload.pop("finished_at", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


__all__ = [
    "EvolutionReport",
    "StepOutcome",
    "StepRecord",
    "compute_replay_hash",
    "detect_convergence",
    "detect_drift",
    "detect_local_optimum",
    "detect_oscillation",
]
