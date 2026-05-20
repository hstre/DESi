"""v3.63 — pair-level failure diversity.

For every plateau-anchor pair, count the number of
failure-profile axes that differ. Closed diversity
axes (matching FailureProfile fields):

* primary_cause              (uniform in this corpus)
* source_corpus
* contradiction_load_at_final
* anchor_density_bucket
* branch_cost_at_final

Maximum diversity score = 5; minimum = 0.

Per-pair resonance is computed at PROBE_RADIUS=3.5 in
the full 9-d trajectory space (matches v3.50/v3.60/v3.61).
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from .failures import (
    FailureProfile, plateau_failure_profiles,
)


PROBE_RADIUS: float = 3.5
DIVERSITY_AXES: tuple[str, ...] = (
    "primary_cause", "source_corpus",
    "contradiction_load_at_final",
    "anchor_density_bucket",
    "branch_cost_at_final",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def pair_diversity(
    a: FailureProfile, b: FailureProfile,
) -> int:
    n = 0
    for axis in DIVERSITY_AXES:
        if getattr(a, axis) != getattr(b, axis):
            n += 1
    return n


def _is_resonant(
    ca: frozenset, cb: frozenset,
) -> bool:
    if not ca or not cb:
        return False
    return not (ca <= cb or cb <= ca)


@dataclass(frozen=True)
class PairDiversityRecord:
    a: str
    b: str
    diversity_score: int
    is_resonant: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "a": self.a, "b": self.b,
            "diversity_score": self.diversity_score,
            "is_resonant": self.is_resonant,
        }


def per_pair_records() -> tuple[
    PairDiversityRecord, ...,
]:
    profiles = {
        p.trajectory_id: p
        for p in plateau_failure_profiles()
    }
    plats = list(collect_plateau_anchors())
    leaks = list(collect_leakage_trajectories())
    leak_vecs = [
        trajectory_vector(t.states) for t in leaks
    ]
    coverages = {}
    for t in plats:
        v = trajectory_vector(t.states)
        coverages[t.trajectory_id] = frozenset(
            i for i, lv in enumerate(leak_vecs)
            if euclidean(v, lv) <= PROBE_RADIUS
        )
    ids = sorted(coverages.keys())
    out: list[PairDiversityRecord] = []
    for a, b in combinations(ids, 2):
        out.append(PairDiversityRecord(
            a=a, b=b,
            diversity_score=pair_diversity(
                profiles[a], profiles[b],
            ),
            is_resonant=_is_resonant(
                coverages[a], coverages[b],
            ),
        ))
    return tuple(out)


def mean_diversity_by_resonance(
) -> tuple[float, float]:
    records = per_pair_records()
    resonant = [
        r.diversity_score for r in records if r.is_resonant
    ]
    non_resonant = [
        r.diversity_score for r in records if not r.is_resonant
    ]
    mean_res = (
        _round(sum(resonant) / len(resonant))
        if resonant else 0.0
    )
    mean_non = (
        _round(sum(non_resonant) / len(non_resonant))
        if non_resonant else 0.0
    )
    return mean_res, mean_non


def diversity_activation_correlation() -> float:
    """Pearson correlation between diversity_score
    and resonance (0/1)."""
    records = per_pair_records()
    n = len(records)
    if n < 2:
        return 0.0
    xs = [r.diversity_score for r in records]
    ys = [1.0 if r.is_resonant else 0.0 for r in records]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(xs, ys)
    )
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return 0.0
    return _round(cov / (var_x ** 0.5 * var_y ** 0.5))


def failure_diversity_score() -> float:
    """Global average diversity score across all
    pairs, normalised to [0, 1]."""
    records = per_pair_records()
    if not records:
        return 0.0
    total = sum(r.diversity_score for r in records)
    max_per_pair = len(DIVERSITY_AXES)
    return _round(
        total / (max_per_pair * len(records)),
    )


def redundancy_score() -> float:
    """1 - failure_diversity_score: fraction of axis-
    matches across pairs."""
    return _round(1.0 - failure_diversity_score())


__all__ = [
    "DIVERSITY_AXES", "PROBE_RADIUS",
    "PairDiversityRecord",
    "diversity_activation_correlation",
    "failure_diversity_score",
    "mean_diversity_by_resonance",
    "pair_diversity", "per_pair_records",
    "redundancy_score",
]
