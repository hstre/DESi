"""v3.123 — multi-signal pre-T10 rule.

Pins the production-facing rule to the closed
search outcome in ``search.best_rule()``. Any
future drift in the search (axis enum, T1, T2
grid, ground-truth labels) flips the pinned axis
or threshold and the regression tests catch it.

The rule has exactly two thresholds (T1 on the
text_variance axis, T2 on a second orthogonal
axis), so ``rule_complexity() == 2``.

Public API mirrors ``pre_t10_rule.rule`` so the
v3.124 deployment comparison can swap rules
without changing call sites.
"""
from __future__ import annotations

from functools import lru_cache

from ..pre_t10_rule.rule import (
    pool_text_variance,
)
from ..state_blindness.census import (
    BlindnessPool, cross_family_pools,
)
from .search import (
    TwoDRule, _AXIS_DIRECTION, axis_value,
    best_rule,
)


@lru_cache(maxsize=1)
def selected_rule() -> TwoDRule:
    return best_rule()


def selected_axis() -> str:
    return selected_rule().axis


def selected_t1() -> float:
    return selected_rule().t1


def selected_t2() -> float:
    return selected_rule().t2


def rule_complexity() -> int:
    """Number of thresholds the rule applies.

    v3.120 had complexity 1 (text_variance only);
    v3.123 has complexity 2 (text_variance plus a
    second axis)."""
    return 2


def rule_allows_t10(pool: BlindnessPool) -> bool:
    """Apply the pinned 2D rule to a pool."""
    r = selected_rule()
    if pool_text_variance(pool) < r.t1:
        return False
    v = axis_value(r.axis, pool)
    direction = _AXIS_DIRECTION[r.axis]
    if direction == ">=":
        return v >= r.t2
    return v <= r.t2


def final_far() -> float:
    return selected_rule().far


def final_tpr() -> float:
    return selected_rule().tpr


def allowed_pool_count() -> int:
    return selected_rule().allowed_count


def blocked_pool_count() -> int:
    return selected_rule().blocked_count


def pools_allowed() -> tuple[
    BlindnessPool, ...,
]:
    return tuple(
        p for p in cross_family_pools()
        if rule_allows_t10(p)
    )


def pools_blocked() -> tuple[
    BlindnessPool, ...,
]:
    return tuple(
        p for p in cross_family_pools()
        if not rule_allows_t10(p)
    )


__all__ = [
    "allowed_pool_count",
    "blocked_pool_count",
    "final_far",
    "final_tpr",
    "pools_allowed",
    "pools_blocked",
    "rule_allows_t10",
    "rule_complexity",
    "selected_axis",
    "selected_rule",
    "selected_t1",
    "selected_t2",
]
