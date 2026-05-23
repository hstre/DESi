"""Single-knob mutation for the v2.0 evolution sandbox.

Aufgabe 2 directive: per step exactly ONE parameter may mutate, and
the only legal target is ``branch_open_evidence_min``. The delta is
small (±0.02) and **deterministic** — derived from a sha256 of the
step id and the parent hash so that an entire 30-step run is bit-for-
bit replayable.

The mutated value is clamped to ``[MIN_VALUE, MAX_VALUE]`` so that
the knob never leaves its v0.7-documented operating range. Clamping
counts as the mutation even when it produces the same numeric value
as the parent — the parameter still appears in ``mutated_parameters``
because the proposal selected it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

MUTABLE_PARAMETER: str = "branch_open_evidence_min"
DELTA: float = 0.02
MIN_VALUE: float = 0.20
MAX_VALUE: float = 0.80
BASELINE_VALUE: float = 0.45   # v0.7 M-001 production setting


def _direction_for(step_id: int, parent_hash: str) -> int:
    """Deterministic ±1 selection from sha256(step_id || parent_hash).

    Even byte → +1, odd byte → -1. Pure function; given the same
    inputs the same direction is returned across runs and machines.
    """
    h = hashlib.sha256(
        f"{step_id}|{parent_hash}".encode("utf-8"),
    ).digest()
    return +1 if (h[0] % 2 == 0) else -1


def _round6(x: float) -> float:
    """Six-decimal rounding to keep canonical-JSON encodings stable."""
    return round(x, 6)


@dataclass(frozen=True)
class MutationProposal:
    """One proposed mutation to apply to a clone before benchmarking.

    The frozen dataclass is the canonical record. ``mutated_parameters``
    is the public hard-invariant surface — its length is checked at
    sandbox runtime to enforce the single-knob rule.
    """

    step_id: int
    parent_hash: str
    parameter: str
    parent_value: float
    proposed_value: float
    delta_applied: float
    direction: int            # +1 or -1
    clamped: bool             # True iff clamping changed the raw value
    mutated_parameters: tuple[str, ...] = field(default=())

    @classmethod
    def build(
        cls,
        *,
        step_id: int,
        parent_hash: str,
        parent_value: float,
    ) -> "MutationProposal":
        direction = _direction_for(step_id, parent_hash)
        raw = _round6(parent_value + direction * DELTA)
        clamped_value = _round6(max(MIN_VALUE, min(MAX_VALUE, raw)))
        return cls(
            step_id=step_id,
            parent_hash=parent_hash,
            parameter=MUTABLE_PARAMETER,
            parent_value=_round6(parent_value),
            proposed_value=clamped_value,
            delta_applied=_round6(clamped_value - parent_value),
            direction=direction,
            clamped=(clamped_value != raw),
            mutated_parameters=(MUTABLE_PARAMETER,),
        )

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if self.parameter != MUTABLE_PARAMETER:
            raise ValueError(
                f"v2.0 forbids mutating {self.parameter!r}; "
                f"only {MUTABLE_PARAMETER!r} is permitted",
            )
        if len(self.mutated_parameters) != 1:
            raise ValueError(
                "single-knob invariant violated: "
                f"mutated_parameters={self.mutated_parameters!r}",
            )
        if self.mutated_parameters[0] != MUTABLE_PARAMETER:
            raise ValueError(
                "mutated_parameters must list "
                f"{MUTABLE_PARAMETER!r}, got {self.mutated_parameters!r}",
            )
        if not (MIN_VALUE <= self.proposed_value <= MAX_VALUE):
            raise ValueError(
                f"proposed_value {self.proposed_value} outside "
                f"[{MIN_VALUE}, {MAX_VALUE}]",
            )
        if self.direction not in (+1, -1):
            raise ValueError(
                f"direction must be +1 or -1, got {self.direction}",
            )

    # ------------------------------------------------------------------
    # Canonical serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "parent_hash": self.parent_hash,
            "parameter": self.parameter,
            "parent_value": self.parent_value,
            "proposed_value": self.proposed_value,
            "delta_applied": self.delta_applied,
            "direction": self.direction,
            "clamped": self.clamped,
            "mutated_parameters": list(self.mutated_parameters),
        }


__all__ = [
    "BASELINE_VALUE",
    "DELTA",
    "MAX_VALUE",
    "MIN_VALUE",
    "MUTABLE_PARAMETER",
    "MutationProposal",
]
