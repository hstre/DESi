"""v3.120 — rule efficacy metrics.

For every v3.117 cross-family pool we compare:

* the ground-truth ``rescuable`` label from
  v3.119 (best AUC across closed taxonomy);
* the proposed pre-T10 rule's decision
  (``rule_allows_t10``).

We derive:

* ``false_activation_rate`` - fraction of
  pools the rule WOULD activate that are NOT
  actually rescuable.
* ``true_case_recall`` - fraction of
  genuinely rescuable pools the rule lets
  through.
* ``historical_gate_flip_count`` - count of
  historical Concept Gate verdicts that would
  flip under the rule. The rule only blocks
  T10 activation; it does not modify gate
  outputs. Hence it is structurally 0.
* ``rule_roi`` - true_case_recall divided by
  (false_activation_rate + epsilon).
"""
from __future__ import annotations

from functools import lru_cache

from ..t10_boundary.boundary import (
    all_pool_recoverability,
)
from .rule import (
    BLINDNESS_CHECK_THRESHOLD,
    rule_allows_t10,
)


_EPSILON: float = 0.01


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def _decision_table() -> list[
    tuple[int, bool, bool, float],
]:
    """List of (pool_id, rescuable, allowed,
    text_variance)."""
    from ..state_blindness.census import (
        cross_family_pools,
    )
    pools_by_id = {
        p.pool_id: p
        for p in cross_family_pools()
    }
    out: list[
        tuple[int, bool, bool, float],
    ] = []
    for pr in all_pool_recoverability():
        p = pools_by_id.get(pr.pool_id)
        if p is None:
            continue
        allowed = rule_allows_t10(p)
        out.append((
            pr.pool_id,
            pr.rescuable,
            allowed,
            pr.text_variance,
        ))
    return out


def false_activation_rate() -> float:
    table = _decision_table()
    allowed = [
        row for row in table if row[2]
    ]
    if not allowed:
        return 0.0
    fa = sum(1 for _, r, _, _ in allowed if not r)
    return _round(fa / len(allowed))


def true_case_recall() -> float:
    table = _decision_table()
    rescuable = [
        row for row in table if row[1]
    ]
    if not rescuable:
        return 0.0
    let_through = sum(
        1 for _, _, a, _ in rescuable if a
    )
    return _round(let_through / len(rescuable))


def historical_gate_flip_count() -> int:
    """The rule blocks activation - it does not
    modify any historical artifact's gate
    outputs. By construction the count is 0."""
    return 0


def rule_roi() -> float:
    fa = false_activation_rate()
    tr = true_case_recall()
    denom = fa + _EPSILON
    return _round(tr / denom)


@lru_cache(maxsize=1)
def blocked_pool_count() -> int:
    table = _decision_table()
    return sum(1 for _, _, a, _ in table if not a)


@lru_cache(maxsize=1)
def allowed_pool_count() -> int:
    table = _decision_table()
    return sum(1 for _, _, a, _ in table if a)


__all__ = [
    "BLINDNESS_CHECK_THRESHOLD",
    "allowed_pool_count",
    "blocked_pool_count",
    "false_activation_rate",
    "historical_gate_flip_count",
    "rule_roi",
    "true_case_recall",
]
