"""v8.2 — closed competing-goals taxonomy.

Six closed optimization goals. The directive
forbids hidden reweighting; the weights are
declared up-front and never mutate, so the
``hidden_reweighting`` Pflichtmetrik is 0 by
construction. A regression that started
modifying ``GOAL_WEIGHTS`` at runtime would
flip this metric.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OptimizationGoal(str, Enum):
    ACCURACY_MAX        = "accuracy_max"
    COST_MIN            = "cost_min"
    SPEED_MAX           = "speed_max"
    CONFLICT_MIN        = "conflict_min"
    COHERENCE_MAX       = "coherence_max"
    EXPLORATION_MAX     = "exploration_max"


OPTIMIZATION_GOALS: tuple[str, ...] = tuple(
    g.value for g in OptimizationGoal
)


# Equal-weight balance. Weights are public,
# pinned, and never re-read at runtime.
GOAL_WEIGHTS: dict[str, float] = {
    OptimizationGoal.ACCURACY_MAX.value: 1.0,
    OptimizationGoal.COST_MIN.value: 1.0,
    OptimizationGoal.SPEED_MAX.value: 1.0,
    OptimizationGoal.CONFLICT_MIN.value: 1.0,
    OptimizationGoal.COHERENCE_MAX.value: 1.0,
    OptimizationGoal.EXPLORATION_MAX.value: 1.0,
}


@dataclass(frozen=True)
class GoalScored:
    item_id: str
    text: str
    scores: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "text": self.text,
            "scores": dict(self.scores),
        }


_FIXTURE: tuple[GoalScored, ...] = (
    GoalScored("g-001",
        "Accurate but slow analysis.",
        scores={
            "accuracy_max": 0.95,
            "cost_min": 0.30,
            "speed_max": 0.20,
            "conflict_min": 0.70,
            "coherence_max": 0.85,
            "exploration_max": 0.40,
        }),
    GoalScored("g-002",
        "Fast but shallow heuristic.",
        scores={
            "accuracy_max": 0.40,
            "cost_min": 0.85,
            "speed_max": 0.90,
            "conflict_min": 0.50,
            "coherence_max": 0.50,
            "exploration_max": 0.30,
        }),
    GoalScored("g-003",
        "Balanced compromise.",
        scores={
            "accuracy_max": 0.70,
            "cost_min": 0.60,
            "speed_max": 0.60,
            "conflict_min": 0.65,
            "coherence_max": 0.70,
            "exploration_max": 0.55,
        }),
    GoalScored("g-004",
        "Exploratory but conflict-heavy.",
        scores={
            "accuracy_max": 0.60,
            "cost_min": 0.40,
            "speed_max": 0.40,
            "conflict_min": 0.25,
            "coherence_max": 0.45,
            "exploration_max": 0.95,
        }),
    GoalScored("g-005",
        "Coherent but conservative.",
        scores={
            "accuracy_max": 0.80,
            "cost_min": 0.55,
            "speed_max": 0.50,
            "conflict_min": 0.85,
            "coherence_max": 0.95,
            "exploration_max": 0.20,
        }),
    GoalScored("g-006",
        "Cheap and conflict-free but bland.",
        scores={
            "accuracy_max": 0.45,
            "cost_min": 0.95,
            "speed_max": 0.75,
            "conflict_min": 0.90,
            "coherence_max": 0.60,
            "exploration_max": 0.25,
        }),
    GoalScored("g-007",
        "High-accuracy exploratory hybrid.",
        scores={
            "accuracy_max": 0.85,
            "cost_min": 0.40,
            "speed_max": 0.35,
            "conflict_min": 0.55,
            "coherence_max": 0.75,
            "exploration_max": 0.80,
        }),
    GoalScored("g-008",
        "Pure speed run.",
        scores={
            "accuracy_max": 0.30,
            "cost_min": 0.90,
            "speed_max": 0.95,
            "conflict_min": 0.60,
            "coherence_max": 0.40,
            "exploration_max": 0.20,
        }),
)


def fixture() -> tuple[GoalScored, ...]:
    return _FIXTURE


__all__ = [
    "GOAL_WEIGHTS",
    "GoalScored",
    "OPTIMIZATION_GOALS",
    "OptimizationGoal",
    "fixture",
]
