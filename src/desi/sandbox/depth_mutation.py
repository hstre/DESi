"""Depth mutation — Aufgabe 2.

Mutates exactly one knob: ``RecursiveResolver.max_depth``.

* ``max_depth ∈ {1, 2, 3, 4, 5, 6}``
* per step ``±1`` only — jumps of 2 or more are forbidden by
  construction (``__post_init__`` rejects them)
* direction deterministically derived from ``sha256(step_id ||
  parent_hash)`` — same discipline as the v2.0 single-knob mutator
* values are clamped to ``[DEPTH_MIN, DEPTH_MAX]`` so the knob never
  leaves the legal range
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

MUTABLE_PARAMETER: str = "RecursiveResolver.max_depth"
DEPTH_MIN: int = 1
DEPTH_MAX: int = 6
DEFAULT_START_DEPTH: int = 3


def _direction_for(step_id: int, parent_hash: str) -> int:
    h = hashlib.sha256(
        f"{step_id}|{parent_hash}".encode("utf-8"),
    ).digest()
    return +1 if (h[0] % 2 == 0) else -1


@dataclass(frozen=True)
class DepthMutationProposal:
    """One proposed ±1 mutation of ``max_depth``."""

    step_id: int
    parent_hash: str
    parameter: str
    parent_depth: int
    proposed_depth: int
    direction: int
    clamped: bool
    mutated_parameters: tuple[str, ...] = field(default=())

    @classmethod
    def build(
        cls,
        *,
        step_id: int,
        parent_hash: str,
        parent_depth: int,
    ) -> "DepthMutationProposal":
        direction = _direction_for(step_id, parent_hash)
        raw = parent_depth + direction
        clamped = max(DEPTH_MIN, min(DEPTH_MAX, raw))
        return cls(
            step_id=step_id,
            parent_hash=parent_hash,
            parameter=MUTABLE_PARAMETER,
            parent_depth=parent_depth,
            proposed_depth=clamped,
            direction=direction,
            clamped=(clamped != raw),
            mutated_parameters=(MUTABLE_PARAMETER,),
        )

    def __post_init__(self) -> None:
        if self.parameter != MUTABLE_PARAMETER:
            raise ValueError(
                f"v2.2 forbids mutating {self.parameter!r}; "
                f"only {MUTABLE_PARAMETER!r} is permitted",
            )
        if len(self.mutated_parameters) != 1:
            raise ValueError(
                "single-knob invariant violated: "
                f"mutated_parameters={self.mutated_parameters!r}",
            )
        if self.mutated_parameters[0] != MUTABLE_PARAMETER:
            raise ValueError(
                f"mutated_parameters must list {MUTABLE_PARAMETER!r}, "
                f"got {self.mutated_parameters!r}",
            )
        if not (DEPTH_MIN <= self.proposed_depth <= DEPTH_MAX):
            raise ValueError(
                f"proposed_depth {self.proposed_depth} outside "
                f"[{DEPTH_MIN}, {DEPTH_MAX}]",
            )
        if not (DEPTH_MIN <= self.parent_depth <= DEPTH_MAX):
            raise ValueError(
                f"parent_depth {self.parent_depth} outside "
                f"[{DEPTH_MIN}, {DEPTH_MAX}]",
            )
        if abs(self.proposed_depth - self.parent_depth) > 1:
            raise ValueError(
                "depth mutation jumps by more than 1: "
                f"{self.parent_depth} -> {self.proposed_depth}",
            )
        if self.direction not in (+1, -1):
            raise ValueError(
                f"direction must be +1 or -1, got {self.direction}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "parent_hash": self.parent_hash,
            "parameter": self.parameter,
            "parent_depth": self.parent_depth,
            "proposed_depth": self.proposed_depth,
            "direction": self.direction,
            "clamped": self.clamped,
            "mutated_parameters": list(self.mutated_parameters),
        }


__all__ = [
    "DEFAULT_START_DEPTH",
    "DEPTH_MAX",
    "DEPTH_MIN",
    "DepthMutationProposal",
    "MUTABLE_PARAMETER",
]
