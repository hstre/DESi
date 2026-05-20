"""v3.104c — stress aggregates."""
from __future__ import annotations

from .stress import (
    StressKind, all_stress_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def stress_adverse_flips_max() -> int:
    outs = all_stress_outcomes()
    if not outs:
        return 0
    return max(o.adverse_flip_count for o in outs)


def stress_beneficial_flips_min() -> int:
    outs = all_stress_outcomes()
    if not outs:
        return 0
    return min(o.beneficial_flip_count for o in outs)


def stress_beneficial_flips_max() -> int:
    outs = all_stress_outcomes()
    if not outs:
        return 0
    return max(o.beneficial_flip_count for o in outs)


def seed_invariance() -> float:
    """1.0 iff every SEED_RESHUFFLE cell shares
    identical adverse/beneficial counts."""
    seed_cells = [
        o for o in all_stress_outcomes()
        if o.kind == StressKind.SEED_RESHUFFLE.value
    ]
    if not seed_cells:
        return 0.0
    ref = (
        seed_cells[0].adverse_flip_count,
        seed_cells[0].beneficial_flip_count,
        seed_cells[0].adverse_auc_delta,
        seed_cells[0].beneficial_auc_delta,
    )
    return _round(
        sum(
            1 for c in seed_cells
            if (
                c.adverse_flip_count,
                c.beneficial_flip_count,
                c.adverse_auc_delta,
                c.beneficial_auc_delta,
            ) == ref
        ) / len(seed_cells),
    )


def order_invariance() -> float:
    """1.0 iff every OUTCOME_PERMUTATION cell
    shares identical aggregates."""
    cells = [
        o for o in all_stress_outcomes()
        if o.kind
        == StressKind.OUTCOME_PERMUTATION.value
    ]
    if not cells:
        return 0.0
    ref = (
        cells[0].adverse_flip_count,
        cells[0].beneficial_flip_count,
    )
    return _round(
        sum(
            1 for c in cells
            if (
                c.adverse_flip_count,
                c.beneficial_flip_count,
            ) == ref
        ) / len(cells),
    )


def reimport_invariance() -> float:
    cells = [
        o for o in all_stress_outcomes()
        if o.kind
        == StressKind.ISOLATED_MODULE_REIMPORT.value
    ]
    if not cells:
        return 0.0
    ref = (
        cells[0].adverse_flip_count,
        cells[0].beneficial_flip_count,
        cells[0].adverse_auc_delta,
        cells[0].beneficial_auc_delta,
    )
    return _round(
        sum(
            1 for c in cells
            if (
                c.adverse_flip_count,
                c.beneficial_flip_count,
                c.adverse_auc_delta,
                c.beneficial_auc_delta,
            ) == ref
        ) / len(cells),
    )


__all__ = [
    "order_invariance",
    "reimport_invariance",
    "seed_invariance",
    "stress_adverse_flips_max",
    "stress_beneficial_flips_max",
    "stress_beneficial_flips_min",
]
