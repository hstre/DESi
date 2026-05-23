"""v3.62 — per-pair coverage overlap aggregation.

Splits the 190 plateau pairs into heterogeneous
(diff_fam) and homogeneous (same_fam) cohorts and
reports mean per-cohort coverage_gain, redundancy,
new_region_fraction. Restricts to ACTIVE pairs (both
anchors with non-empty coverage) so the coverage
metrics are well-defined.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..cross_corpus.corpus_loader import (
    normalised_prefix,
)
from .coverage import (
    PairCoverage, all_anchor_coverages,
    pair_coverage,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class CohortBlindspot:
    cohort: str          # "heterogeneous" | "homogeneous"
    active_pair_count: int
    total_pair_count: int
    mean_coverage_gain: float
    mean_redundancy: float
    mean_new_region_fraction: float
    sum_symmetric_diff: int

    def to_dict(self) -> dict[str, object]:
        return {
            "cohort": self.cohort,
            "active_pair_count":
                self.active_pair_count,
            "total_pair_count":
                self.total_pair_count,
            "mean_coverage_gain":
                self.mean_coverage_gain,
            "mean_redundancy":
                self.mean_redundancy,
            "mean_new_region_fraction":
                self.mean_new_region_fraction,
            "sum_symmetric_diff":
                self.sum_symmetric_diff,
        }


def all_pair_records() -> tuple[PairCoverage, ...]:
    covs = all_anchor_coverages()
    return tuple(
        pair_coverage(a, b)
        for a, b in combinations(covs, 2)
    )


def _is_heterogeneous(a: str, b: str) -> bool:
    return normalised_prefix(a) != normalised_prefix(b)


def _summarise(
    cohort: str, pairs: list[PairCoverage],
    total: int,
) -> CohortBlindspot:
    if not pairs:
        return CohortBlindspot(
            cohort=cohort, active_pair_count=0,
            total_pair_count=total,
            mean_coverage_gain=0.0,
            mean_redundancy=0.0,
            mean_new_region_fraction=0.0,
            sum_symmetric_diff=0,
        )
    gains = [p.coverage_gain for p in pairs]
    reds = [p.redundancy for p in pairs]
    news = [p.new_region_fraction for p in pairs]
    sds = [p.symmetric_diff_size for p in pairs]
    return CohortBlindspot(
        cohort=cohort, active_pair_count=len(pairs),
        total_pair_count=total,
        mean_coverage_gain=_round(
            sum(gains) / len(gains),
        ),
        mean_redundancy=_round(
            sum(reds) / len(reds),
        ),
        mean_new_region_fraction=_round(
            sum(news) / len(news),
        ),
        sum_symmetric_diff=sum(sds),
    )


def cohort_blindspots() -> tuple[
    CohortBlindspot, CohortBlindspot,
]:
    records = all_pair_records()
    het_total = sum(
        1 for p in records
        if _is_heterogeneous(p.a, p.b)
    )
    hom_total = sum(
        1 for p in records
        if not _is_heterogeneous(p.a, p.b)
    )
    het_active = [
        p for p in records
        if _is_heterogeneous(p.a, p.b)
        and p.size_a > 0 and p.size_b > 0
    ]
    hom_active = [
        p for p in records
        if not _is_heterogeneous(p.a, p.b)
        and p.size_a > 0 and p.size_b > 0
    ]
    return (
        _summarise(
            "heterogeneous", het_active, het_total,
        ),
        _summarise(
            "homogeneous", hom_active, hom_total,
        ),
    )


__all__ = [
    "CohortBlindspot", "all_pair_records",
    "cohort_blindspots",
]
