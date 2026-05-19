"""v15.3 - exploration budget and search reduction.

A human audit team can examine only a fraction of
the brute-force universe. DESi spends that budget
on the highest-priority cells (after the
recoverability discount), pruning zero-priority
redundant cells entirely.

* audit_search_reduction = 1 - audited / universe
* cost_reduction_proxy = depth-weighted reduction
  (deep dives into strong signals cost more, so
  the cost saving is smaller than the count
  saving - an honest accounting).

Reads no post-hoc label.
"""
from __future__ import annotations

from functools import lru_cache

from .audit_priority import audit_universe, universe_size
from .risk_ranking import RankedCell, ranked_cells

# The auditor can examine this fraction of the
# brute-force universe.
BUDGET_FRACTION = 0.40
# Depth-of-audit cost weight: a flagged cell costs
# 1 + COST_DEPTH * signal to examine.
COST_DEPTH = 4.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def budget_size() -> int:
    return round(BUDGET_FRACTION * universe_size())


@lru_cache(maxsize=1)
def selected_cells() -> tuple[RankedCell, ...]:
    """Top cells within budget, ignoring cells that
    the discount has driven to zero priority (no
    point spending budget on a fully recoverable
    redundant cell)."""
    budget = budget_size()
    positive = [
        r for r in ranked_cells() if r.priority > 0.0
    ]
    return tuple(positive[:budget])


@lru_cache(maxsize=1)
def selected_keys() -> frozenset[tuple[str, str]]:
    return frozenset(
        (r.firm_id, r.axis) for r in selected_cells()
    )


def audit_search_reduction() -> float:
    total = universe_size()
    if total == 0:
        return 0.0
    audited = len(selected_cells())
    return _round(1.0 - audited / total)


def _cell_cost(value: float) -> float:
    return 1.0 + COST_DEPTH * value


def cost_reduction_proxy() -> float:
    """1 - (cost of audited cells / cost of the
    whole universe), with depth-weighted cost."""
    universe = audit_universe()
    if not universe:
        return 0.0
    total_cost = sum(
        _cell_cost(c.value) for c in universe
    )
    sel = selected_keys()
    audited_cost = sum(
        _cell_cost(c.value)
        for c in universe
        if (c.firm_id, c.axis) in sel
    )
    if total_cost <= 0:
        return 0.0
    return _round(1.0 - audited_cost / total_cost)


__all__ = [
    "BUDGET_FRACTION",
    "audit_search_reduction",
    "budget_size",
    "cost_reduction_proxy",
    "selected_cells",
    "selected_keys",
]
