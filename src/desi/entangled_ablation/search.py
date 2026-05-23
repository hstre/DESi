"""v3.94 — exhaustive subset search over the 9
state dimensions.

Closed search:

* sizes 1, 2, 3 ⇒ ``C(9,1)+C(9,2)+C(9,3) = 129``
  distinct subsets.

For each subset we record the cluster count,
sizes, and purity. Ties are broken by (purity desc,
size asc, alphabetical asc) so the search is
fully deterministic.
"""
from __future__ import annotations

import itertools
from functools import lru_cache

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from .ablation import (
    AblationOutcome, baseline_purity,
    cluster_entangled_with, cluster_purity,
)


MAX_SUBSET_SIZE: int = 3


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def all_subset_outcomes() -> tuple[
    AblationOutcome, ...,
]:
    out: list[AblationOutcome] = []
    for k in range(1, MAX_SUBSET_SIZE + 1):
        for combo in itertools.combinations(
            DIMENSION_NAMES, k,
        ):
            keep = frozenset(combo)
            clusters = cluster_entangled_with(keep)
            out.append(AblationOutcome(
                dims=tuple(sorted(combo)),
                dim_count=k,
                cluster_count=len(clusters),
                cluster_sizes=tuple(
                    len(c.members)
                    for c in clusters
                ),
                purity=cluster_purity(clusters),
            ))
    return tuple(out)


def best_outcome() -> AblationOutcome:
    """Highest purity; among ties, smallest dim
    count; then alphabetical."""
    outs = all_subset_outcomes()
    return max(
        outs,
        key=lambda o: (
            o.purity, -o.dim_count,
            tuple(reversed(sorted(o.dims))),
        ),
    )


def best_dim_set() -> tuple[str, ...]:
    return best_outcome().dims


def best_purity() -> float:
    return best_outcome().purity


def dimensionality_cost() -> int:
    """Smallest dim count among all subsets that
    achieve the best purity."""
    best = best_purity()
    outs = all_subset_outcomes()
    eligible = [
        o.dim_count
        for o in outs if o.purity == best
    ]
    return min(eligible) if eligible else 0


def stability() -> float:
    """Fraction of subsets that tie the best
    purity. Higher = more subsets agree on the
    ceiling; 1.0 means every subset is at the
    ceiling (genuine doppelganger - nothing
    separates the families)."""
    outs = all_subset_outcomes()
    best = best_purity()
    if not outs:
        return 0.0
    ties = sum(1 for o in outs if o.purity == best)
    return _round(ties / len(outs))


def purity_above_baseline_count() -> int:
    """Number of subsets that strictly beat the
    majority-class baseline. If zero, no state-
    vector subset separates the families."""
    base = baseline_purity()
    return sum(
        1 for o in all_subset_outcomes()
        if o.purity > base
    )


__all__ = [
    "MAX_SUBSET_SIZE",
    "all_subset_outcomes",
    "best_dim_set", "best_outcome",
    "best_purity", "dimensionality_cost",
    "purity_above_baseline_count",
    "stability",
]
