"""Aufgaben 6 + 8 — distribution metrics for the residue."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .cases import ResidueCase
from .classifier import Classification
from .enums import ResidualSemanticFailure


@dataclass(frozen=True)
class DistributionSummary:
    total: int
    failure_count: dict[str, int]
    failure_entropy: float
    largest_cluster: float
    largest_cluster_class: str
    singleton_count: int
    per_domain: dict[str, dict[str, int]]
    unknown_fraction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "failure_count": dict(self.failure_count),
            "failure_entropy": self.failure_entropy,
            "largest_cluster": self.largest_cluster,
            "largest_cluster_class": self.largest_cluster_class,
            "singleton_count": self.singleton_count,
            "per_domain": {
                k: dict(v) for k, v in self.per_domain.items()
            },
            "unknown_fraction": self.unknown_fraction,
        }


def _entropy(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    out = 0.0
    for c in counts.values():
        if c == 0:
            continue
        p = c / total
        out -= p * math.log2(p)
    return round(out, 6)


def summarise(
    cases: tuple[ResidueCase, ...],
    classifications: tuple[Classification, ...],
) -> DistributionSummary:
    counts: dict[str, int] = {}
    per_domain: dict[str, dict[str, int]] = {}
    for c, cls in zip(cases, classifications):
        counts[cls.failure_class] = (
            counts.get(cls.failure_class, 0) + 1
        )
        slot = per_domain.setdefault(c.domain, {})
        slot[cls.failure_class] = (
            slot.get(cls.failure_class, 0) + 1
        )
    total = sum(counts.values())
    if counts:
        largest_kv = max(counts.items(), key=lambda kv: kv[1])
    else:
        largest_kv = (
            ResidualSemanticFailure.UNKNOWN.value, 0,
        )
    largest_fraction = (
        round(largest_kv[1] / total, 6) if total else 0.0
    )
    singletons = sum(1 for v in counts.values() if v == 1)
    entropy = _entropy(counts)
    unknown = counts.get(
        ResidualSemanticFailure.UNKNOWN.value, 0,
    )
    unknown_fraction = (
        round(unknown / total, 6) if total else 1.0
    )
    return DistributionSummary(
        total=total,
        failure_count={k: counts[k] for k in sorted(counts)},
        failure_entropy=entropy,
        largest_cluster=largest_fraction,
        largest_cluster_class=largest_kv[0],
        singleton_count=singletons,
        per_domain={
            k: dict(per_domain[k])
            for k in sorted(per_domain)
        },
        unknown_fraction=unknown_fraction,
    )


__all__ = ["DistributionSummary", "summarise"]
