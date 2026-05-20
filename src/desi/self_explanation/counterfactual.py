"""v3.37 — counterfactual generator + per-dimension diff.

Given a trajectory and Strategy B (apply_k_holds with
k=1), produce a counterfactual trace and a closed list
of per-dimension deltas. No theory; pure observation of
which state-vector components the intervention moves.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)
from ..plateau_hold_sweep.hold_sweep import apply_k_holds


@dataclass(frozen=True)
class DimensionDelta:
    dimension: str          # value from DIMENSION_NAMES
    index: int
    original: float
    counterfactual: float

    @property
    def magnitude(self) -> float:
        return abs(self.counterfactual - self.original)

    def to_dict(self) -> dict[str, object]:
        return {
            "dimension": self.dimension,
            "index": self.index,
            "original": self.original,
            "counterfactual": self.counterfactual,
            "magnitude": self.magnitude,
        }


def strategy_b_counterfactual(
    states: tuple[StateVector, ...],
) -> tuple[StateVector, ...]:
    """The single intervention under audit (v3.35
    Strategy B = v3.34 B1_ONE_HOLD)."""
    return apply_k_holds(states, 1)


def per_dimension_deltas(
    original: tuple[StateVector, ...],
    counterfactual: tuple[StateVector, ...],
) -> tuple[DimensionDelta, ...]:
    """All (dimension, index) pairs where the
    counterfactual differs from the original."""
    out: list[DimensionDelta] = []
    if len(original) != len(counterfactual):
        return tuple(out)
    for i, (so, sc) in enumerate(
        zip(original, counterfactual),
    ):
        for dim in DIMENSION_NAMES:
            o = getattr(so, dim)
            c = getattr(sc, dim)
            if o != c:
                out.append(DimensionDelta(
                    dimension=dim, index=i,
                    original=o, counterfactual=c,
                ))
    return tuple(out)


__all__ = [
    "DimensionDelta", "per_dimension_deltas",
    "strategy_b_counterfactual",
]
