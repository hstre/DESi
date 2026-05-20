"""DepthEvolutionReport — Aufgabe 9.

Twelve mandatory fields plus a deterministic ``replay_hash`` so
that two runs of the same depth-sandbox configuration produce the
identical artifact.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DepthStepOutcome(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    KILLED = "killed"
    PLATEAU_HOLD = "plateau_hold"   # accepted-no-change (zero delta)


@dataclass(frozen=True)
class DepthStepRecord:
    step_id: int
    parent_depth: int
    proposed_depth: int
    accepted_depth: int
    direction: int
    clamped: bool
    outcome: DepthStepOutcome
    fitness: float
    fitness_killed: bool
    resolved_depth_cases: int
    cycle_detection_correct: int
    blocked_propagation_correct: int
    mean_resolution_depth: float
    max_resolution_depth: int
    cycle_detection_rate: float
    blocked_propagation_rate: float
    depth_exceeded_rate: float
    resolution_complete_rate: float
    main_false_positives: int
    main_hash_mismatches: int
    main_authority_blocks: int
    failure_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "parent_depth": self.parent_depth,
            "proposed_depth": self.proposed_depth,
            "accepted_depth": self.accepted_depth,
            "direction": self.direction,
            "clamped": self.clamped,
            "outcome": self.outcome.value,
            "fitness": (
                "-inf" if self.fitness_killed
                else round(self.fitness, 6)
            ),
            "fitness_killed": self.fitness_killed,
            "resolved_depth_cases": self.resolved_depth_cases,
            "cycle_detection_correct": self.cycle_detection_correct,
            "blocked_propagation_correct":
                self.blocked_propagation_correct,
            "mean_resolution_depth": self.mean_resolution_depth,
            "max_resolution_depth": self.max_resolution_depth,
            "cycle_detection_rate": self.cycle_detection_rate,
            "blocked_propagation_rate": self.blocked_propagation_rate,
            "depth_exceeded_rate": self.depth_exceeded_rate,
            "resolution_complete_rate": self.resolution_complete_rate,
            "main_false_positives": self.main_false_positives,
            "main_hash_mismatches": self.main_hash_mismatches,
            "main_authority_blocks": self.main_authority_blocks,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class DepthEvolutionReport:
    started_at: datetime
    finished_at: datetime
    stable_version: str
    stable_hash_before: str
    stable_hash_after: str
    total_steps: int
    accepted_steps: int
    rejected_steps: int
    killed_steps: int
    best_depth: int
    starting_depth: int
    depth_history: tuple[int, ...]
    plateau_detected: bool
    oscillation_detected: bool
    convergence_detected: bool
    best_fitness: float
    recommended_depth: int
    steps: tuple[DepthStepRecord, ...] = field(default_factory=tuple)
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
            "best_depth": self.best_depth,
            "starting_depth": self.starting_depth,
            "depth_history": list(self.depth_history),
            "plateau_detected": self.plateau_detected,
            "oscillation_detected": self.oscillation_detected,
            "convergence_detected": self.convergence_detected,
            "best_fitness": round(self.best_fitness, 6),
            "recommended_depth": self.recommended_depth,
            "steps": [s.to_dict() for s in self.steps],
            "replay_hash": self.replay_hash,
            "reflection": self.reflection,
        }


def compute_depth_replay_hash(payload: dict[str, Any]) -> str:
    """Deterministic 16-hex hash. Excludes timestamps + replay_hash."""
    cleaned = {k: v for k, v in payload.items()
               if k not in ("started_at", "finished_at", "replay_hash")}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def detect_oscillation(depth_history: list[int]) -> bool:
    if len(depth_history) < 4:
        return False
    deltas = [b - a for a, b in zip(depth_history, depth_history[1:])
              if (b - a) != 0]
    reversals = sum(
        1 for x, y in zip(deltas, deltas[1:]) if (x > 0) != (y > 0)
    )
    return reversals >= 3


def detect_convergence(depth_history: list[int], window: int = 5) -> bool:
    if len(depth_history) < window:
        return False
    tail = depth_history[-window:]
    return max(tail) == min(tail)


__all__ = [
    "DepthEvolutionReport",
    "DepthStepOutcome",
    "DepthStepRecord",
    "compute_depth_replay_hash",
    "detect_convergence",
    "detect_oscillation",
]
