"""v28.3 - the comparison benchmark table.

Assembles the per-dimension DESi_current vs DESi_candidate table
(current, candidate, delta, direction, verdict). Deterministic;
the candidate column is a projection, not a measured system.
"""
from __future__ import annotations

from dataclasses import dataclass

from .evolution_metrics import (
    DIMENSIONS, HIGHER_IS_BETTER, SAFETY_INVARIANTS,
    candidate_vector, current_vector, is_better, is_worse,
)


@dataclass(frozen=True)
class DimensionRow:
    dimension: str
    current: float
    candidate: float
    delta: float
    higher_is_better: bool
    is_safety_invariant: bool
    verdict: str  # "improved" | "held" | "degraded"

    def to_dict(self) -> dict[str, object]:
        return {
            "dimension": self.dimension,
            "current": self.current,
            "candidate": self.candidate,
            "delta": self.delta,
            "higher_is_better": self.higher_is_better,
            "is_safety_invariant": self.is_safety_invariant,
            "verdict": self.verdict,
        }


def comparison_table() -> tuple[DimensionRow, ...]:
    cur, cand = current_vector(), candidate_vector()
    rows: list[DimensionRow] = []
    for d in DIMENSIONS:
        if is_better(d, cand[d], cur[d]):
            verdict = "improved"
        elif is_worse(d, cand[d], cur[d]):
            verdict = "degraded"
        else:
            verdict = "held"
        rows.append(DimensionRow(
            dimension=d,
            current=cur[d],
            candidate=cand[d],
            delta=round(cand[d] - cur[d], 6),
            higher_is_better=HIGHER_IS_BETTER[d],
            is_safety_invariant=d in SAFETY_INVARIANTS,
            verdict=verdict,
        ))
    return tuple(rows)


__all__ = [
    "DimensionRow",
    "comparison_table",
]
