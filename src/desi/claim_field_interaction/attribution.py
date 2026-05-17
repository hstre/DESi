"""v3.45 — per-anchor mass attribution.

For each plateau anchor, count how many overcontrolled
(leakage) trajectories it would capture in isolation at
the probe radius. The ranked list answers the
directive's self-question:

    "Which claim changed this trajectory most?"

A claim with high per-anchor leakage count is
dominant — its activation contributes the most to the
field leakage.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .mass import PROBE_RADIUS, ordered_plateau_anchors


_SUPPORTED = 4.0


@dataclass(frozen=True)
class AnchorContribution:
    anchor_id: str
    leakage_count: int
    leakage_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "leakage_count": self.leakage_count,
            "leakage_ids": list(self.leakage_ids),
        }


def per_anchor_leakage(
) -> tuple[AnchorContribution, ...]:
    pids = set(plateau_trajectory_ids())
    leaks: list = []
    for t in extract_all_trajectories():
        if t.trajectory_id in pids:
            continue
        if t.states[-1].support_state == _SUPPORTED:
            leaks.append(
                (t.trajectory_id, trajectory_vector(t.states)),
            )
    out: list[AnchorContribution] = []
    for anchor in ordered_plateau_anchors():
        av = trajectory_vector(anchor.states)
        captured: list[str] = []
        for lid, lv in leaks:
            if euclidean(av, lv) <= PROBE_RADIUS:
                captured.append(lid)
        captured.sort()
        out.append(AnchorContribution(
            anchor_id=anchor.trajectory_id,
            leakage_count=len(captured),
            leakage_ids=tuple(captured),
        ))
    return tuple(out)


def dominant_anchors(
    contributions: tuple[AnchorContribution, ...],
    limit: int = 5,
) -> tuple[str, ...]:
    """Top ``limit`` anchors by per-anchor leakage
    count. Ties broken by ``anchor_id`` for
    determinism."""
    ranked = sorted(
        contributions,
        key=lambda c: (-c.leakage_count, c.anchor_id),
    )
    return tuple(c.anchor_id for c in ranked[:limit])


__all__ = [
    "AnchorContribution", "dominant_anchors",
    "per_anchor_leakage",
]
