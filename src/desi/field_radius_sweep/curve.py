"""v3.44 — leakage & recall curves over the radius
sweep.

Per radius:

* ``leakage_count``    — number of SUPPORTED non-
  plateau cases the policy moves
* ``plateau_recall``   — fraction of the 20 plateau
  cases the policy resolves
* ``leakage_reduction`` — 1 - leakage_count / baseline,
  where baseline = leakage_count at radius=inf

``optimal_radius`` is the SMALLEST radius (from the
closed RADII set) that simultaneously:

  * preserves plateau_recall >= MIN_PLATEAU_RECALL, and
  * keeps leakage_count == 0 (or, more generally, the
    minimum observed leakage across the sweep).

If no such radius exists the field hypothesis is weak
and the report records ``optimal_radius = None``.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import inf

from .ablation import RadiusOutcome
from .radius import RADII, radius_label


MIN_PLATEAU_RECALL = 0.90


@dataclass(frozen=True)
class RadiusPoint:
    radius: float
    radius_label: str
    plateau_resolved_count: int
    leakage_count: int
    plateau_recall: float
    leakage_reduction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "radius": (
                "inf" if self.radius == inf
                else self.radius
            ),
            "radius_label": self.radius_label,
            "plateau_resolved_count":
                self.plateau_resolved_count,
            "leakage_count": self.leakage_count,
            "plateau_recall": self.plateau_recall,
            "leakage_reduction":
                self.leakage_reduction,
        }


def compute_curve(
    outcomes: tuple[RadiusOutcome, ...],
    plateau_population: int,
) -> tuple[RadiusPoint, ...]:
    by_radius: dict[str, list[RadiusOutcome]] = {}
    for o in outcomes:
        by_radius.setdefault(
            o.radius_label, [],
        ).append(o)
    # Baseline = inf
    baseline_leakage = sum(
        1 for o in by_radius.get("inf", [])
        if o.leakage
    )
    points: list[RadiusPoint] = []
    for r in RADII:
        lbl = radius_label(r)
        items = by_radius.get(lbl, [])
        res = sum(
            1 for o in items if o.plateau_resolved
        )
        leak = sum(1 for o in items if o.leakage)
        recall = (
            round(res / plateau_population, 6)
            if plateau_population else 0.0
        )
        red = (
            round(1.0 - leak / baseline_leakage, 6)
            if baseline_leakage else 1.0
        )
        points.append(RadiusPoint(
            radius=r, radius_label=lbl,
            plateau_resolved_count=res,
            leakage_count=leak, plateau_recall=recall,
            leakage_reduction=red,
        ))
    return tuple(points)


def pick_optimal_radius(
    curve: tuple[RadiusPoint, ...],
) -> RadiusPoint | None:
    """Smallest radius in the closed set that meets
    both eligibility predicates. Ties broken by lower
    radius (a tighter ball is preferred)."""
    eligible = [
        p for p in curve
        if p.plateau_recall >= MIN_PLATEAU_RECALL
        and p.leakage_count == 0
    ]
    if not eligible:
        return None
    return min(eligible, key=lambda p: p.radius)


def pick_largest_clean_radius(
    curve: tuple[RadiusPoint, ...],
) -> RadiusPoint | None:
    """Largest radius that keeps leakage_count == 0
    and full recall. The sweet-spot interpretation:
    the broadest geometric ball that still excludes
    the leakage cohort."""
    eligible = [
        p for p in curve
        if p.plateau_recall >= MIN_PLATEAU_RECALL
        and p.leakage_count == 0
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda p: p.radius)


__all__ = [
    "MIN_PLATEAU_RECALL", "RadiusPoint",
    "compute_curve", "pick_largest_clean_radius",
    "pick_optimal_radius",
]
