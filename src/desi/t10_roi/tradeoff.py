"""v3.104 — recovery / complexity / ROI metrics
for T10.

* ``recovery_gain`` - sum of beneficial AUC and
  purity deltas across the v3.94 / v3.96 /
  v3.100 gates that T10 was designed to rescue.
* ``architecture_roi`` - recovery_gain divided
  by the structural cost
  (state_dim_cost + compression_delta +
  overfitting_risk). Higher = better trade-off.
"""
from __future__ import annotations

from ..t10_compat.replay import (
    all_historical_gate_outcomes,
    beneficial_flip_count,
)
from .complexity import (
    compression_delta, overfitting_risk,
    state_dim_cost,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_RESCUE_TARGET_SPRINTS: frozenset[str] = (
    frozenset({
        "v3.94 entangled_ablation",
        "v3.96 entangled_resolution",
        "v3.100 compression_audit",
    })
)


def recovery_gain() -> float:
    """Sum of |counterfactual - stored| for the
    targeted rescue sprints. Positive ⇒ T10
    improves the metric."""
    outs = all_historical_gate_outcomes()
    total = 0.0
    for o in outs:
        if o.sprint_id not in _RESCUE_TARGET_SPRINTS:
            continue
        delta = abs(
            o.counterfactual_value
            - o.stored_value,
        )
        total += delta
    return _round(total)


def complexity_cost() -> float:
    """Mean of the closed cost components."""
    parts = (
        state_dim_cost(),
        compression_delta(),
        overfitting_risk(),
    )
    return _round(sum(parts) / len(parts))


def architecture_roi() -> float:
    cost = complexity_cost()
    if cost <= 0.0:
        return 0.0
    return _round(recovery_gain() / cost)


__all__ = [
    "architecture_roi",
    "complexity_cost",
    "recovery_gain",
]
