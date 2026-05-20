"""v3.119 — re-exports for clarity."""
from __future__ import annotations

from .scope import (
    PoolRecoverability,
    all_pool_recoverability,
    blindness_prediction_auc,
    false_negative_rate,
    false_positive_rate,
    recoverability_threshold,
)


def rescuable_pool_count() -> int:
    return sum(
        1 for o in all_pool_recoverability()
        if o.rescuable
    )


def unrescuable_pool_count() -> int:
    return sum(
        1 for o in all_pool_recoverability()
        if not o.rescuable
    )


__all__ = [
    "PoolRecoverability",
    "all_pool_recoverability",
    "blindness_prediction_auc",
    "false_negative_rate",
    "false_positive_rate",
    "recoverability_threshold",
    "rescuable_pool_count",
    "unrescuable_pool_count",
]
