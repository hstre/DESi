"""v3.52 — phase curve construction.

Per mass level ``k``, compute:

* ``leakage_count``        — |union of coverage of
  the first k anchors|
* ``additive_prediction``  — sum of per-anchor sizes
  for the first k anchors (no overlap discount)
* ``plateau_recall``       — fraction of plateau
  trajectories captured (always 1.0 once k >= 1
  because each plateau anchor sits at distance 0
  from itself)
* ``coupling_at_k``        — 1 - leakage_count /
  additive_prediction (subadditivity ratio)
"""
from __future__ import annotations

from dataclasses import dataclass

from ..field_leakage.census import collect_plateau_anchors
from ..field_leakage.distance import (
    manifold_distance, trajectory_vector,
)
from ..pair_resonance.coverage import (
    AnchorCoverage, coverage_for_subset,
    per_anchor_coverage,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .mass import (
    PROBE_RADIUS, all_mass_levels, first_k_ids,
)


def _plateau_self_recall(
    radius: float, k: int,
) -> float:
    """Fraction of plateau anchors within radius of
    the first-k active anchor set."""
    anchors = list(collect_plateau_anchors())
    anchors.sort(key=lambda t: t.trajectory_id)
    plat_vecs = tuple(
        trajectory_vector(t.states) for t in anchors
    )
    if k <= 0:
        return 0.0
    active = plat_vecs[:k]
    captured = sum(
        1 for v in plat_vecs
        if manifold_distance(v, active)[0] <= radius
    )
    return _round(captured / len(plat_vecs))


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class PhasePoint:
    mass_level: int
    leakage_count: int
    additive_prediction: int
    plateau_recall: float
    coupling_at_k: float

    def to_dict(self) -> dict[str, object]:
        return {
            "mass_level": self.mass_level,
            "leakage_count": self.leakage_count,
            "additive_prediction":
                self.additive_prediction,
            "plateau_recall": self.plateau_recall,
            "coupling_at_k": self.coupling_at_k,
        }


def compute_phase_curve(
    radius: float = PROBE_RADIUS,
) -> tuple[PhasePoint, ...]:
    coverages = per_anchor_coverage(radius)
    by_id = {c.anchor_id: c for c in coverages}
    pids = set(plateau_trajectory_ids())
    plateau_pop = len(pids)
    out: list[PhasePoint] = []
    for k in all_mass_levels():
        ids = first_k_ids(k)
        union = coverage_for_subset(coverages, ids)
        leak = len(union)
        additive = sum(
            by_id[i].size for i in ids if i in by_id
        )
        coupling = (
            _round(1.0 - leak / additive)
            if additive > 0 else 0.0
        )
        recall = _plateau_self_recall(radius, k)
        out.append(PhasePoint(
            mass_level=k, leakage_count=leak,
            additive_prediction=additive,
            plateau_recall=recall,
            coupling_at_k=coupling,
        ))
    return tuple(out)


def discontinuity_score(
    curve: tuple[PhasePoint, ...],
) -> float:
    """max(|leakage(k+1) - leakage(k)|) / max_leakage.
    1.0 means a single discrete jump accounts for all
    leakage growth; 0.0 means perfectly smooth."""
    if len(curve) < 2:
        return 0.0
    max_leak = max(p.leakage_count for p in curve)
    if max_leak == 0:
        return 0.0
    deltas = [
        abs(curve[i + 1].leakage_count
            - curve[i].leakage_count)
        for i in range(len(curve) - 1)
    ]
    return _round(max(deltas) / max_leak)


def saturation_point(
    curve: tuple[PhasePoint, ...],
) -> int | None:
    """Smallest mass_level whose leakage equals the
    asymptotic maximum across the curve."""
    if not curve:
        return None
    max_leak = max(p.leakage_count for p in curve)
    if max_leak == 0:
        return None
    for p in curve:
        if p.leakage_count >= max_leak:
            return p.mass_level
    return None


def coupling_strength(
    curve: tuple[PhasePoint, ...],
) -> float:
    """Overall subadditivity across the sweep:
    1 - sum(leakage(k)) / sum(additive(k)) over
    positive-additive mass levels."""
    sum_leak = sum(
        p.leakage_count for p in curve
        if p.additive_prediction > 0
    )
    sum_add = sum(
        p.additive_prediction for p in curve
        if p.additive_prediction > 0
    )
    if sum_add == 0:
        return 0.0
    return _round(1.0 - sum_leak / sum_add)


__all__ = [
    "PhasePoint", "compute_phase_curve",
    "coupling_strength", "discontinuity_score",
    "saturation_point",
]
