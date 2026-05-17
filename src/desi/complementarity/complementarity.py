"""v3.61 — complementarity decomposition.

Splits the 190 plateau-anchor pairs into the closed
2×2 grid of (distance bucket × corpus-family bucket)
and measures per-cell resonance rate. The directive's
four conditions:

* ``high_d / same_fam``  — geometric distance only
  (distance contribution with family controlled)
* ``low_d / diff_fam``   — heterogeneity only
  (family contribution with distance controlled)
* ``high_d / diff_fam``  — combined
* ``low_d / same_fam``   — baseline
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..cross_corpus.corpus_loader import (
    normalised_prefix,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from .distance import distance_bucket


PROBE_RADIUS: float = 3.5


def _is_resonant(
    ca: frozenset, cb: frozenset,
) -> bool:
    if not ca or not cb:
        return False
    return not (ca <= cb or cb <= ca)


def _coverage_set(
    anchor_vec: tuple[float, ...],
    leakage_vecs: list[tuple[float, ...]],
    radius: float,
) -> frozenset[int]:
    return frozenset(
        i for i, lv in enumerate(leakage_vecs)
        if euclidean(anchor_vec, lv) <= radius
    )


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ConditionCell:
    condition: str          # "high_d_same_fam" etc.
    pair_count: int
    resonant_pair_count: int
    activation_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "condition": self.condition,
            "pair_count": self.pair_count,
            "resonant_pair_count":
                self.resonant_pair_count,
            "activation_rate": self.activation_rate,
        }


def _family_bucket(a: str, b: str) -> str:
    return (
        "same_fam"
        if normalised_prefix(a) == normalised_prefix(b)
        else "diff_fam"
    )


def per_cell_results(
    radius: float = PROBE_RADIUS,
) -> tuple[ConditionCell, ...]:
    plats = list(collect_plateau_anchors())
    leaks = list(collect_leakage_trajectories())
    leakage_vecs = [
        trajectory_vector(t.states) for t in leaks
    ]
    plat_vecs = {
        t.trajectory_id: trajectory_vector(t.states)
        for t in plats
    }
    coverages = {
        pid: _coverage_set(
            av, leakage_vecs, radius,
        )
        for pid, av in plat_vecs.items()
    }
    cells: dict[str, list[bool]] = {
        f"{d}_{f}": []
        for d in ("high_d", "low_d")
        for f in ("same_fam", "diff_fam")
    }
    ids = sorted(plat_vecs.keys())
    for a, b in combinations(ids, 2):
        d_cat = distance_bucket(
            euclidean(plat_vecs[a], plat_vecs[b]),
        )
        f_cat = _family_bucket(a, b)
        cells[f"{d_cat}_{f_cat}"].append(
            _is_resonant(coverages[a], coverages[b]),
        )
    out: list[ConditionCell] = []
    for cond in (
        "high_d_same_fam", "low_d_same_fam",
        "high_d_diff_fam", "low_d_diff_fam",
    ):
        items = cells[cond]
        n = len(items)
        n_res = sum(1 for x in items if x)
        rate = _round(n_res / n) if n > 0 else 0.0
        out.append(ConditionCell(
            condition=cond, pair_count=n,
            resonant_pair_count=n_res,
            activation_rate=rate,
        ))
    return tuple(out)


def distance_only_activation(
    cells: tuple[ConditionCell, ...],
) -> float:
    """Effect of distance with family controlled
    (same_fam): rate(high_d) - rate(low_d)."""
    by = {c.condition: c for c in cells}
    h = by["high_d_same_fam"].activation_rate
    l = by["low_d_same_fam"].activation_rate
    return _round(h - l)


def heterogeneity_only_activation(
    cells: tuple[ConditionCell, ...],
) -> float:
    """Effect of family with distance controlled
    (low_d): rate(diff_fam) - rate(same_fam)."""
    by = {c.condition: c for c in cells}
    d = by["low_d_diff_fam"].activation_rate
    s = by["low_d_same_fam"].activation_rate
    return _round(d - s)


def combined_activation(
    cells: tuple[ConditionCell, ...],
) -> float:
    """Joint cell: rate(high_d, diff_fam)."""
    by = {c.condition: c for c in cells}
    return by["high_d_diff_fam"].activation_rate


def baseline_activation(
    cells: tuple[ConditionCell, ...],
) -> float:
    by = {c.condition: c for c in cells}
    return by["low_d_same_fam"].activation_rate


def best_explanation_model(
    cells: tuple[ConditionCell, ...],
) -> str:
    """Closed verdict over which factor dominates."""
    d = distance_only_activation(cells)
    h = heterogeneity_only_activation(cells)
    combo = combined_activation(cells)
    base = baseline_activation(cells)
    interaction = combo - max(d + base, h + base)
    if combo == 0 and d == 0 and h == 0:
        return "NULL"
    if combo > max(d, h) + base * 0.5 + 0.05:
        return "COMBINED"
    if d > h + 0.05:
        return "DISTANCE_DOMINANT"
    if h > d + 0.05:
        return "HETEROGENEITY_DOMINANT"
    return "DISTANCE_AND_HETEROGENEITY"


__all__ = [
    "ConditionCell", "PROBE_RADIUS",
    "baseline_activation",
    "best_explanation_model", "combined_activation",
    "distance_only_activation",
    "heterogeneity_only_activation",
    "per_cell_results",
]
