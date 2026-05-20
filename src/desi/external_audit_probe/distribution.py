"""Aufgabe 6 — distribution analysis.

Computes the closed-taxonomy distribution metrics: per-class
counts, Shannon entropy, largest cluster (as fraction of the
corpus), singleton count, per-domain distribution, and the
cross-strategy agreement on failure class.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .cases import FalseSupportCase
from .classifier import Classification
from .enums import ExternalAuditFailure


@dataclass(frozen=True)
class DistributionSummary:
    total: int
    failure_count: dict[str, int]
    failure_entropy: float
    largest_cluster: float
    largest_cluster_class: str
    singleton_count: int
    per_domain: dict[str, dict[str, int]]
    cross_strategy_agreement: float

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
            "cross_strategy_agreement":
                self.cross_strategy_agreement,
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
    cases: tuple[FalseSupportCase, ...],
    classifications: tuple[Classification, ...],
    strategy_origins: dict[str, tuple[str, ...]],
) -> DistributionSummary:
    """``strategy_origins`` maps chain_id → tuple of v4.1
    strategy ids that unlocked the case as a false support.
    The cross-strategy agreement is the fraction of cases
    unlocked by *all four* v4.1 strategies (the failure-class
    assignment is text-only and therefore strategy-invariant;
    the meaningful agreement is on *whether* the strategy
    even routes the chain into the audit at all)."""
    counts: dict[str, int] = {
        f.value: 0 for f in ExternalAuditFailure
    }
    per_domain: dict[str, dict[str, int]] = {}
    for c, cls in zip(cases, classifications):
        counts[cls.failure_class] = (
            counts.get(cls.failure_class, 0) + 1
        )
        per = per_domain.setdefault(c.domain, {})
        per[cls.failure_class] = per.get(cls.failure_class, 0) + 1
    nonzero = {k: v for k, v in counts.items() if v > 0}
    total = sum(nonzero.values())
    largest_class = (
        max(nonzero.items(), key=lambda kv: kv[1])
        if nonzero else (ExternalAuditFailure.UNKNOWN.value, 0)
    )
    largest_fraction = (
        round(largest_class[1] / total, 6) if total else 0.0
    )
    singletons = sum(1 for v in nonzero.values() if v == 1)
    entropy = _entropy(nonzero)
    full_strategy_unlock = sum(
        1 for c in cases
        if len(strategy_origins.get(c.chain_id, ())) == 4
    )
    cross_agreement = (
        round(full_strategy_unlock / len(cases), 6)
        if cases else 0.0
    )
    return DistributionSummary(
        total=total,
        failure_count={k: nonzero[k] for k in sorted(nonzero)},
        failure_entropy=entropy,
        largest_cluster=largest_fraction,
        largest_cluster_class=largest_class[0],
        singleton_count=singletons,
        per_domain={
            k: dict(per_domain[k])
            for k in sorted(per_domain)
        },
        cross_strategy_agreement=cross_agreement,
    )


__all__ = ["DistributionSummary", "summarise"]
