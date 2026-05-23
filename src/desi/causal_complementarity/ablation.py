"""v3.64 — closed-set causal ablation.

For every plateau-anchor pair we record four factor
levels (matching the directive's A/B/C/D ablations):

* ``A_distance``       — high_d / low_d bucket
* ``B_heterogeneity``  — same_fam / diff_fam
* ``C_diversity``      — failure-profile diversity
  score (0..5)
* ``D_coverage_gain``  — |A union B| - max(|A|, |B|)

An ablation restricts the universe to the subset
where factor X has no informative variation. We
report ``resonant_rate_after`` per ablation and
``causal_importance`` = 1 - rate_after / baseline_rate.

Subsets with fewer than ``MIN_SUBSET_FOR_INFERENCE``
pairs are flagged as ``LOW_POWER`` so a 100% drop on
6 pairs is not over-interpreted.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..complementarity.distance import (
    distance_bucket, plateau_pair_distances,
)
from ..cross_corpus.corpus_loader import (
    normalised_prefix,
)
from ..failure_diversity.diversity import (
    pair_diversity,
)
from ..failure_diversity.failures import (
    plateau_failure_profiles,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


PROBE_RADIUS: float = 3.5
MIN_SUBSET_FOR_INFERENCE: int = 30
NECESSARY_IMPORTANCE_FLOOR: float = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _is_resonant(
    ca: frozenset, cb: frozenset,
) -> bool:
    if not ca or not cb:
        return False
    return not (ca <= cb or cb <= ca)


@dataclass(frozen=True)
class PairFactors:
    a: str
    b: str
    distance_bucket: str
    same_family: bool
    diversity_score: int
    coverage_gain: int
    has_overlap: bool
    is_resonant: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "a": self.a, "b": self.b,
            "distance_bucket": self.distance_bucket,
            "same_family": self.same_family,
            "diversity_score": self.diversity_score,
            "coverage_gain": self.coverage_gain,
            "has_overlap": self.has_overlap,
            "is_resonant": self.is_resonant,
        }


def all_pair_factors() -> tuple[PairFactors, ...]:
    plats = list(collect_plateau_anchors())
    leaks = list(collect_leakage_trajectories())
    pv = {
        t.trajectory_id: trajectory_vector(t.states)
        for t in plats
    }
    lv = [
        trajectory_vector(t.states) for t in leaks
    ]
    coverages = {
        pid: frozenset(
            i for i, l in enumerate(lv)
            if euclidean(av, l) <= PROBE_RADIUS
        )
        for pid, av in pv.items()
    }
    profiles = {
        p.trajectory_id: p
        for p in plateau_failure_profiles()
    }
    pair_dists: dict = {}
    for d in plateau_pair_distances():
        pair_dists[(d.a, d.b)] = d.distance
        pair_dists[(d.b, d.a)] = d.distance
    ids = sorted(pv.keys())
    out: list[PairFactors] = []
    for a, b in combinations(ids, 2):
        ca, cb = coverages[a], coverages[b]
        out.append(PairFactors(
            a=a, b=b,
            distance_bucket=distance_bucket(
                pair_dists[(a, b)],
            ),
            same_family=(
                normalised_prefix(a)
                == normalised_prefix(b)
            ),
            diversity_score=pair_diversity(
                profiles[a], profiles[b],
            ),
            coverage_gain=(
                len(ca | cb)
                - max(len(ca), len(cb))
            ),
            has_overlap=bool(ca & cb),
            is_resonant=_is_resonant(ca, cb),
        ))
    return tuple(out)


@dataclass(frozen=True)
class AblationResult:
    factor: str               # "A_distance" etc.
    subset_size: int
    resonant_after: int
    rate_after: float
    causal_importance: float
    low_power: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "factor": self.factor,
            "subset_size": self.subset_size,
            "resonant_after": self.resonant_after,
            "rate_after": self.rate_after,
            "causal_importance":
                self.causal_importance,
            "low_power": self.low_power,
        }


def _ablate_to(
    pairs: tuple[PairFactors, ...],
    predicate,
) -> tuple[int, int]:
    subset = [p for p in pairs if predicate(p)]
    n = len(subset)
    res = sum(1 for p in subset if p.is_resonant)
    return n, res


def run_ablations() -> tuple[AblationResult, ...]:
    pairs = all_pair_factors()
    baseline_total = len(pairs)
    baseline_res = sum(
        1 for p in pairs if p.is_resonant
    )
    baseline_rate = (
        baseline_res / baseline_total
        if baseline_total else 0.0
    )
    factors = [
        ("A_distance", lambda p: p.distance_bucket == "low_d"),
        ("B_heterogeneity", lambda p: p.same_family),
        ("C_diversity", lambda p: p.diversity_score == 0),
        ("D_coverage_gain", lambda p: p.coverage_gain <= 0),
    ]
    out: list[AblationResult] = []
    for name, pred in factors:
        n, res = _ablate_to(pairs, pred)
        rate = res / n if n > 0 else 0.0
        importance = (
            _round(1.0 - rate / baseline_rate)
            if baseline_rate > 0 else 0.0
        )
        out.append(AblationResult(
            factor=name, subset_size=n,
            resonant_after=res,
            rate_after=_round(rate),
            causal_importance=importance,
            low_power=(
                n < MIN_SUBSET_FOR_INFERENCE
            ),
        ))
    return tuple(out)


def baseline_resonance() -> int:
    return sum(
        1 for p in all_pair_factors() if p.is_resonant
    )


def baseline_pair_count() -> int:
    return len(all_pair_factors())


def necessary_factors(
    results: tuple[AblationResult, ...],
) -> tuple[str, ...]:
    return tuple(
        r.factor for r in results
        if r.causal_importance >= NECESSARY_IMPORTANCE_FLOOR
        and not r.low_power
    )


def sufficient_factors(
    results: tuple[AblationResult, ...],
) -> tuple[str, ...]:
    """A factor is "sufficient" if its PRESENCE alone
    in the highest-power subset still produces
    resonance comparable to baseline. We implement
    sufficiency as the converse of importance: subsets
    that PRESERVE the factor and ablate the others
    should retain resonance. For the single-factor
    case we take: subset where the factor's "high"
    value holds AND other factors are at their ablated
    levels."""
    pairs = all_pair_factors()
    baseline = sum(
        1 for p in pairs if p.is_resonant
    )
    if baseline == 0:
        return ()
    base_rate = baseline / len(pairs)
    # Try each factor as the "preserved" one
    factors_with_pred = [
        ("A_distance",
         lambda p: (
             p.distance_bucket == "high_d"
             and p.same_family
             and p.diversity_score == 0
             and p.coverage_gain <= 0
         )),
        ("B_heterogeneity",
         lambda p: (
             not p.same_family
             and p.distance_bucket == "low_d"
             and p.diversity_score == 0
             and p.coverage_gain <= 0
         )),
        ("C_diversity",
         lambda p: (
             p.diversity_score > 0
             and p.distance_bucket == "low_d"
             and p.same_family
             and p.coverage_gain <= 0
         )),
        ("D_coverage_gain",
         lambda p: (
             p.coverage_gain > 0
             and p.distance_bucket == "low_d"
             and p.same_family
             and p.diversity_score == 0
         )),
    ]
    out: list[str] = []
    for name, pred in factors_with_pred:
        subset = [p for p in pairs if pred(p)]
        if not subset:
            continue
        res = sum(
            1 for p in subset if p.is_resonant
        )
        if (res / len(subset)) >= base_rate:
            out.append(name)
    return tuple(out)


__all__ = [
    "AblationResult", "MIN_SUBSET_FOR_INFERENCE",
    "NECESSARY_IMPORTANCE_FLOOR", "PROBE_RADIUS",
    "PairFactors", "all_pair_factors",
    "baseline_pair_count", "baseline_resonance",
    "necessary_factors", "run_ablations",
    "sufficient_factors",
]
