"""v8.2 — closed-weight optimisation pass."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .goal_conflicts import (
    GOAL_WEIGHTS, OPTIMIZATION_GOALS,
    GoalScored, fixture,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class OptimisedItem:
    item_id: str
    scores: dict[str, float]
    composite: float
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "scores": dict(self.scores),
            "composite": self.composite,
            "rationale": self.rationale,
        }


def _composite(scores: dict[str, float]) -> float:
    total_w = sum(GOAL_WEIGHTS.values())
    if total_w == 0:
        return 0.0
    return _round(
        sum(
            scores[k] * GOAL_WEIGHTS[k]
            for k in GOAL_WEIGHTS
        ) / total_w,
    )


def _rationale(scores: dict[str, float]) -> str:
    parts = [
        f"{k}={scores[k]}"
        for k in OPTIMIZATION_GOALS
    ]
    return (
        "composite from " + ", ".join(parts)
    )


@lru_cache(maxsize=1)
def optimised() -> tuple[OptimisedItem, ...]:
    return tuple(
        OptimisedItem(
            item_id=c.item_id,
            scores=c.scores,
            composite=_composite(c.scores),
            rationale=_rationale(c.scores),
        )
        for c in fixture()
    )


def selected_top_k(k: int = 3) -> tuple[
    OptimisedItem, ...,
]:
    return tuple(sorted(
        optimised(),
        key=lambda x: (-x.composite, x.item_id),
    )[:k])


__all__ = [
    "OptimisedItem",
    "optimised",
    "selected_top_k",
]
