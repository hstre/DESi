"""v38.1 - real cost scorecard for the Granite run.

Cost comes from the real OpenRouter usage captured per call. Granite
is meant to be cheap; cost efficiency is the fraction of tasks whose
real cost stays under a generous per-task budget.
"""
from __future__ import annotations

from .granite_runner import results

# Generous per-task budget in USD; Granite calls cost ~1e-6..3e-6.
_BUDGET_USD = 1e-4


def total_cost() -> float:
    return round(sum(r.cost for r in results()), 9)


def avg_cost() -> float:
    rs = results()
    return round(total_cost() / len(rs), 9) if rs else 0.0


def cost_efficiency() -> float:
    rs = results()
    if not rs:
        return 0.0
    ok = sum(1 for r in rs if r.cost <= _BUDGET_USD)
    return round(ok / len(rs), 6)


def per_task_cost() -> dict[str, float]:
    return {r.task_id: r.cost for r in results()}


__all__ = [
    "avg_cost",
    "cost_efficiency",
    "per_task_cost",
    "total_cost",
]
