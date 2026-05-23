"""v10.0 — trust hierarchy + fairness metrics.

Trust layers are determined by the assigned role
(AUDITOR > PROPOSER > REPLICATOR > REGISTRAR >
DISSENTER) but the trust SCORE is independent
of role and depends on institutional
transparency. The fairness metric compares
trust scores across the role hierarchy; if
trust correlates with role rather than with
transparency, the metric drops.
"""
from __future__ import annotations

import math

from .institutions import fixture
from .roles import (
    INSTITUTIONAL_ROLES, role_assignments,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def trust_per_institution() -> dict[
    str, float,
]:
    return {
        i.institution_id: i.trust_index
        for i in fixture()
    }


def power_concentration() -> float:
    """Maximum institutional power share, minus
    a baseline of perfectly uniform distribution.
    A balanced ecosystem with N institutions
    would have each at 1/N power; anything above
    that is concentration."""
    shares = [i.power_share for i in fixture()]
    if not shares:
        return 0.0
    n = len(shares)
    baseline = 1.0 / n
    excess = max(shares) - baseline
    return _round(max(0.0, excess))


def trust_fairness() -> float:
    """A fair trust assignment is one where
    trust does NOT correlate strongly with
    institutional power_share. We compute
    abs(Pearson(power, trust)) and clip at 0.
    Low value => fair (trust independent of
    power)."""
    insts = fixture()
    if not insts:
        return 1.0
    xs = [i.power_share for i in insts]
    ys = [i.trust_index for i in insts]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum(
        (xs[i] - mx) * (ys[i] - my)
        for i in range(len(xs))
    )
    sx = math.sqrt(sum(
        (x - mx) ** 2 for x in xs
    ))
    sy = math.sqrt(sum(
        (y - my) ** 2 for y in ys
    ))
    if sx == 0 or sy == 0:
        return 1.0
    corr = abs(num / (sx * sy))
    return _round(max(0.0, 1.0 - corr))


def epistemic_equality() -> float:
    """Normalised entropy of the resource_share
    distribution. 1.0 = uniform; 0.0 = single
    institution holds all resources."""
    shares = [
        i.resource_share for i in fixture()
    ]
    total = sum(shares)
    if total <= 0:
        return 0.0
    h = 0.0
    for s in shares:
        p = s / total
        if p > 0:
            h -= p * math.log2(p)
    max_h = math.log2(max(len(shares), 2))
    if max_h <= 0:
        return 0.0
    return _round(h / max_h)


def governance_transparency() -> float:
    """Mean transparency_score across all
    institutions."""
    scores = [
        i.transparency_score for i in fixture()
    ]
    if not scores:
        return 0.0
    return _round(sum(scores) / len(scores))


def role_distribution_balance() -> float:
    """Normalised entropy of the role
    distribution. 1.0 = perfectly balanced."""
    from collections import Counter
    counts = Counter(
        r.role for r in role_assignments()
    )
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    max_h = math.log2(
        max(len(INSTITUTIONAL_ROLES), 2),
    )
    if max_h <= 0:
        return 0.0
    return _round(h / max_h)


__all__ = [
    "epistemic_equality",
    "governance_transparency",
    "power_concentration",
    "role_distribution_balance",
    "trust_fairness",
    "trust_per_institution",
]
