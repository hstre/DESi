"""v38.3 - cost optimisation over real captured costs.

Three honest, complementary cost views, all from real OpenRouter
usage:

* routing_cost_reduction      - the MEAN per-task fractional saving
                                versus always using DeepSeek (the
                                standard cost-aware-routing metric;
                                tasks that need DeepSeek save nothing).
* total_workload_cost_reduction - total-dollar saving on this exact
                                workload (small here because the few
                                hard semantic tasks dominate cost).
* routed_down_efficiency      - saving specifically on the tasks DESi
                                routes down to the cheap model.

Nothing is hidden: all three are reported.
"""
from __future__ import annotations

from .routing_engine import ROUTE_GRANITE, routed_tasks


def routed_cost() -> float:
    return round(sum(t.routed_cost for t in routed_tasks()), 9)


def all_deepseek_cost() -> float:
    return round(sum(t.deepseek_cost for t in routed_tasks()), 9)


def all_granite_cost() -> float:
    return round(sum(t.granite_cost for t in routed_tasks()), 9)


def _task_saving(deepseek_cost: float, routed: float) -> float:
    if deepseek_cost <= 0:
        return 0.0
    return (deepseek_cost - routed) / deepseek_cost


def routing_cost_reduction() -> float:
    """Mean per-task fractional cost saving versus always-DeepSeek."""
    tasks = routed_tasks()
    if not tasks:
        return 0.0
    savings = [
        _task_saving(t.deepseek_cost, t.routed_cost) for t in tasks
    ]
    return round(sum(savings) / len(savings), 6)


def total_workload_cost_reduction() -> float:
    base = all_deepseek_cost()
    if base <= 0:
        return 0.0
    return round((base - routed_cost()) / base, 6)


def routed_down_efficiency() -> float:
    """Saving on the tasks DESi routes down to the cheap model."""
    down = [t for t in routed_tasks() if t.routed_model == ROUTE_GRANITE]
    base = sum(t.deepseek_cost for t in down)
    if base <= 0:
        return 0.0
    spent = sum(t.routed_cost for t in down)
    return round((base - spent) / base, 6)


__all__ = [
    "all_deepseek_cost",
    "all_granite_cost",
    "routed_cost",
    "routed_down_efficiency",
    "routing_cost_reduction",
    "total_workload_cost_reduction",
]
