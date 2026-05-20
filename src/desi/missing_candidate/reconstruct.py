"""v3.75 — candidate reconstruction harness.

For each v3.74 Localization (with non-empty orphan
set), build a CandidateObject and a CandidateMatch.
"""
from __future__ import annotations

from ..field_leakage.census import (
    collect_leakage_trajectories,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)
from ..missing_claim.remove import (
    PROBE_RADIUS, _gather_vectors,
)
from ..missing_localization.localize import (
    all_localizations,
)
from .candidate import (
    CandidateMatch, CandidateObject,
    compare_to_actual, reconstruct_candidate,
)


def _actual_coverage(anchor_id: str) -> int:
    plat_vecs, leak_vecs = _gather_vectors()
    av = plat_vecs.get(anchor_id)
    if av is None:
        return 0
    return sum(
        1 for l in leak_vecs
        if euclidean(av, l) <= PROBE_RADIUS
    )


def _actual_is_bridge(
    anchor_id: str, role: str,
) -> bool:
    return role == "bridge"


def all_candidate_matches() -> tuple[
    CandidateMatch, ...,
]:
    out: list[CandidateMatch] = []
    for loc in all_localizations():
        candidate = reconstruct_candidate(loc)
        if candidate.orphan_count == 0:
            continue
        out.append(compare_to_actual(
            candidate,
            actual_coverage=_actual_coverage(
                loc.removed_id,
            ),
            actual_is_bridge=_actual_is_bridge(
                loc.removed_id, loc.role,
            ),
        ))
    return tuple(out)


__all__ = [
    "all_candidate_matches",
]
