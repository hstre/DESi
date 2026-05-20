"""v15.1 - bridge_evolution_integrity signal.

Disclosure bridges (the explanations that connect
a headline claim to its supporting detail) evolve
over the years. Healthy firms keep coverage
(provided / required) high and stable. A firm
whose required bridges balloon while provided
stagnates is letting its disclosure DEGRADE - an
audit-worthy evolution, NOT a fraud claim.

bridge_evolution_integrity rewards high, stable
coverage and penalises a downward trend.

Reads only the synthetic trajectory.
"""
from __future__ import annotations

from .trajectory import (
    NarrativeTrajectory, trajectories,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _coverage(year) -> float:  # noqa: ANN001
    req = year.bridges_required
    if req <= 0:
        return 1.0
    return _clip01(year.bridges_provided / req)


def bridge_evolution_integrity_firm(
    tr: NarrativeTrajectory,
) -> float:
    """Mean coverage minus half the peak-to-final
    degradation, in [0, 1]. High = coverage is
    strong and did not slide."""
    if not tr.years:
        return 1.0
    covs = [_coverage(y) for y in tr.years]
    mean_cov = sum(covs) / len(covs)
    degradation = max(0.0, covs[0] - covs[-1])
    return _round(_clip01(
        mean_cov - 0.5 * degradation,
    ))


def bridge_evolution_integrity() -> float:
    """Corpus mean of per-firm bridge-evolution
    integrity."""
    trs = trajectories()
    if not trs:
        return 1.0
    vals = [
        bridge_evolution_integrity_firm(t)
        for t in trs
    ]
    return _round(sum(vals) / len(vals))


__all__ = [
    "bridge_evolution_integrity",
    "bridge_evolution_integrity_firm",
]
