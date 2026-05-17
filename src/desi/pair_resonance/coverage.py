"""v3.50 — per-anchor coverage primitives.

A plateau anchor's "coverage" at probe radius r is
the closed set of leakage trajectory ids whose
trajectory_vector falls within Euclidean distance r
of the anchor. The 20 plateau anchors and 145 leakage
trajectories form a 20 × 145 incidence matrix
(implicit; we store per-anchor sets).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


PROBE_RADIUS: float = 3.5
"""Below 3.683 (v3.43 max_manifold_distance), per-
anchor coverage spreads across a wider range than the
saturated regime at r=4.0 — 0, 12, and 121 leakages
per anchor instead of {121, 133, 145}. The pair-
resonance structure is only visible inside this
discrimination band; at r=4.0 every pair includes at
least one universal-coverage anchor and the
resonant-pair count collapses to 0."""


@dataclass(frozen=True)
class AnchorCoverage:
    anchor_id: str
    coverage: frozenset[str]

    @property
    def size(self) -> int:
        return len(self.coverage)


def _leakage_vectors() -> list[tuple[str, tuple[float, ...]]]:
    return [
        (t.trajectory_id, trajectory_vector(t.states))
        for t in collect_leakage_trajectories()
    ]


def per_anchor_coverage(
    radius: float = PROBE_RADIUS,
) -> tuple[AnchorCoverage, ...]:
    leak = _leakage_vectors()
    out: list[AnchorCoverage] = []
    for anchor in collect_plateau_anchors():
        av = trajectory_vector(anchor.states)
        captured = frozenset(
            lid for lid, lv in leak
            if euclidean(av, lv) <= radius
        )
        out.append(AnchorCoverage(
            anchor_id=anchor.trajectory_id,
            coverage=captured,
        ))
    return tuple(out)


def coverage_for_subset(
    coverages: tuple[AnchorCoverage, ...],
    ids: tuple[str, ...],
) -> frozenset[str]:
    """Union of coverage sets for ``ids``. Anchors not
    present in ``coverages`` contribute nothing."""
    by_id = {c.anchor_id: c for c in coverages}
    out: set[str] = set()
    for aid in ids:
        c = by_id.get(aid)
        if c is None:
            continue
        out.update(c.coverage)
    return frozenset(out)


def _trajectory_by_id() -> dict:
    return {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }


def control_anchor_coverage(
    control_ids: tuple[str, ...],
    radius: float = PROBE_RADIUS,
) -> tuple[AnchorCoverage, ...]:
    """Same primitive but using arbitrary trajectory
    ids as anchors. Used by the random-control probe to
    contrast against the plateau anchors."""
    trajs = _trajectory_by_id()
    leak = _leakage_vectors()
    out: list[AnchorCoverage] = []
    for cid in control_ids:
        t = trajs.get(cid)
        if t is None:
            continue
        av = trajectory_vector(t.states)
        captured = frozenset(
            lid for lid, lv in leak
            if euclidean(av, lv) <= radius
        )
        out.append(AnchorCoverage(
            anchor_id=cid, coverage=captured,
        ))
    return tuple(out)


__all__ = [
    "AnchorCoverage", "PROBE_RADIUS",
    "control_anchor_coverage", "coverage_for_subset",
    "per_anchor_coverage",
]
