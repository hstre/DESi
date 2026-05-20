"""v5.0 — adolescence sandbox state and session
data structures.

The sandbox is a closed, deterministic substrate
for DESi to explore in. Every step is described
by a ``TrajectoryStep`` and every reachable state
is described by a ``SandboxState``. State
transitions are pure functions of ``(state,
action, step)`` so the entire trajectory can be
replayed and rolled back to any prior step.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SandboxAction(str, Enum):
    OBSERVE        = "observe"
    HYPOTHESIZE    = "hypothesize"
    CHECKPOINT     = "checkpoint"
    NOOP           = "noop"


ACTIONS: tuple[str, ...] = tuple(
    a.value for a in SandboxAction
)


@dataclass(frozen=True)
class SessionConfig:
    session_id: str
    seed: int
    step_count: int
    checkpoint_every: int = 5

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "seed": self.seed,
            "step_count": self.step_count,
            "checkpoint_every":
                self.checkpoint_every,
        }


@dataclass(frozen=True)
class TrajectoryStep:
    step: int
    action: str
    payload: str
    state_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "action": self.action,
            "payload": self.payload,
            "state_hash": self.state_hash,
        }


@dataclass(frozen=True)
class Snapshot:
    step: int
    state_hash: str
    label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "state_hash": self.state_hash,
            "label": self.label,
        }


@dataclass(frozen=True)
class Session:
    config: SessionConfig
    initial_hash: str
    final_hash: str
    trajectory: tuple[TrajectoryStep, ...]
    snapshots: tuple[Snapshot, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "initial_hash": self.initial_hash,
            "final_hash": self.final_hash,
            "trajectory": [
                s.to_dict()
                for s in self.trajectory
            ],
            "snapshots": [
                s.to_dict()
                for s in self.snapshots
            ],
        }


__all__ = [
    "ACTIONS",
    "SandboxAction",
    "Session",
    "SessionConfig",
    "Snapshot",
    "TrajectoryStep",
]
