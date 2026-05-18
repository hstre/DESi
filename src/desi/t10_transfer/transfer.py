"""v3.106 — transfer aggregates."""
from __future__ import annotations

from .inject import (
    TransferOutcome,
    all_transfer_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def transfer_rate() -> float:
    outs = all_transfer_outcomes()
    if not outs:
        return 0.0
    rescued = sum(1 for o in outs if o.rescued)
    return _round(rescued / len(outs))


def mean_auc_gain() -> float:
    outs = all_transfer_outcomes()
    if not outs:
        return 0.0
    gains = [o.auc_gain for o in outs]
    return _round(sum(gains) / len(gains))


def rescued_cases() -> tuple[
    tuple[str, str], ...,
]:
    return tuple(
        (o.family_a, o.family_b)
        for o in all_transfer_outcomes()
        if o.rescued
    )


def failed_cases() -> tuple[
    tuple[str, str], ...,
]:
    return tuple(
        (o.family_a, o.family_b)
        for o in all_transfer_outcomes()
        if not o.rescued
    )


__all__ = [
    "failed_cases",
    "mean_auc_gain",
    "rescued_cases",
    "transfer_rate",
]
