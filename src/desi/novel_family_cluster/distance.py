"""v3.86 — distance primitives over the v3.85 novel
anchor pool.

We re-use the v3.81 tail-vector representation and
the v3.81 largest-gap threshold rule so the
clustering algorithm itself is the same one that
worked on the plateau cohort. The only thing that
changes is the input pool.
"""
from __future__ import annotations

from ..doppelgaenger.equivalence import (
    largest_gap_threshold, pairwise_distances,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..field_leakage.distance import (
    trajectory_vector,
)
from ..novel_families import all_novel_anchors


def novel_anchor_vectors(
) -> dict[str, tuple[float, ...]]:
    anchors = set(all_novel_anchors())
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
        if t.trajectory_id in anchors
    }


def novel_pairwise_distances() -> tuple[
    tuple[str, str, float], ...,
]:
    return pairwise_distances(novel_anchor_vectors())


def novel_distance_gap() -> float:
    return largest_gap_threshold(
        novel_pairwise_distances(),
    )


__all__ = [
    "novel_anchor_vectors",
    "novel_distance_gap",
    "novel_pairwise_distances",
]
