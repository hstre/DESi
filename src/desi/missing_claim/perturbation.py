"""v3.73 — perturbation aggregation across removals.

Wraps the removal harness with per-role and total
aggregations used by the report.
"""
from __future__ import annotations

from .remove import (
    ClaimRole, RemovalOutcome, TEST_CLAIM_SET,
    all_removal_outcomes, support_shift,
    _gather_vectors,
)


def aggregate() -> tuple[
    tuple[RemovalOutcome, ...], dict[str, float],
]:
    outcomes = all_removal_outcomes()
    per_role = {
        o.role: o.perturbation_magnitude
        for o in outcomes
    }
    return outcomes, per_role


def total_support_shift() -> int:
    plat_vecs, leak_vecs = _gather_vectors()
    set_ids = tuple(aid for aid, _ in TEST_CLAIM_SET)
    return sum(
        support_shift(
            set_ids, plat_vecs, leak_vecs, removed_id,
        )
        for removed_id in set_ids
    )


__all__ = [
    "aggregate", "total_support_shift",
]
