"""v38.3 - escalation logic.

DESi escalates to the large model (DeepSeek) only for high-complexity
tasks; low-complexity structured tasks stay on the cheap model
(Granite). Unnecessary escalations are avoided.
"""
from __future__ import annotations

from .routing_engine import (
    COMPLEXITY_HIGH, ROUTE_DEEPSEEK, RoutedTask, routed_tasks,
)


def should_escalate(task: RoutedTask) -> bool:
    return task.complexity == COMPLEXITY_HIGH


def escalated() -> tuple[RoutedTask, ...]:
    return tuple(
        t for t in routed_tasks() if t.routed_model == ROUTE_DEEPSEEK
    )


def deepseek_escalation_rate() -> float:
    tasks = routed_tasks()
    if not tasks:
        return 0.0
    esc = sum(1 for t in tasks if t.routed_model == ROUTE_DEEPSEEK)
    return round(esc / len(tasks), 6)


def unnecessary_escalations() -> int:
    """A structured (low-complexity) task that was escalated would be
    an unnecessary escalation."""
    return sum(
        1 for t in routed_tasks()
        if t.routed_model == ROUTE_DEEPSEEK and not should_escalate(t)
    )


__all__ = [
    "deepseek_escalation_rate",
    "escalated",
    "should_escalate",
    "unnecessary_escalations",
]
