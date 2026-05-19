"""DESi v8.2 - goal competition (read-only)."""
from __future__ import annotations

from .goal_conflicts import (
    GOAL_WEIGHTS, GoalScored,
    OPTIMIZATION_GOALS, OptimizationGoal,
    fixture,
)
from .optimization import (
    OptimisedItem, optimised, selected_top_k,
)
from .priority import (
    goal_balance, goodhart_risk,
    hidden_reweighting,
    tradeoff_transparency,
)
from .report import (
    V82Report,
    build_goal_competition_artifact,
    build_report,
)


__all__ = [
    "GOAL_WEIGHTS",
    "GoalScored",
    "OPTIMIZATION_GOALS",
    "OptimisedItem",
    "OptimizationGoal",
    "V82Report",
    "build_goal_competition_artifact",
    "build_report",
    "fixture",
    "goal_balance",
    "goodhart_risk",
    "hidden_reweighting",
    "optimised",
    "selected_top_k",
    "tradeoff_transparency",
]
