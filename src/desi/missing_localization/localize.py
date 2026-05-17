"""v3.74 — localization from perturbation centroid.

Given the v3.73 removal harness, for each removal:

1. Find the leakage trajectories that became
   uncovered (or whose nearest distance grew).
2. Compute the centroid of those affected trajectory
   vectors as the PREDICTED missing-region location.
3. Rank the test-set anchors by distance from the
   predicted location. Top-1 is the localization.

DESi does not see the removed anchor's id — only the
perturbed leakage set.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..field_leakage.distance import euclidean
from ..missing_claim.remove import (
    PROBE_RADIUS, TEST_CLAIM_SET,
    _gather_vectors, baseline_coverage,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class Localization:
    removed_id: str
    role: str
    orphan_count: int
    centroid: tuple[float, ...]
    candidate_distances: tuple[tuple[str, float], ...]
    predicted_id: str
    predicted_correct: bool
    hole_region_distance: float

    def to_dict(self) -> dict[str, object]:
        return {
            "removed_id": self.removed_id,
            "role": self.role,
            "orphan_count": self.orphan_count,
            "centroid": list(self.centroid),
            "candidate_distances": [
                {"anchor_id": a, "distance": d}
                for a, d in self.candidate_distances
            ],
            "predicted_id": self.predicted_id,
            "predicted_correct":
                self.predicted_correct,
            "hole_region_distance":
                self.hole_region_distance,
        }


def _centroid(
    vecs: list[tuple[float, ...]],
) -> tuple[float, ...]:
    if not vecs:
        return ()
    n = len(vecs)
    d = len(vecs[0])
    return tuple(
        sum(v[i] for v in vecs) / n
        for i in range(d)
    )


def localize_removal(
    removed_id: str, role: str,
    plat_vecs: dict[str, tuple[float, ...]],
    leak_vecs: list[tuple[float, ...]],
    set_ids: tuple[str, ...],
    radius: float = PROBE_RADIUS,
) -> Localization:
    baseline = baseline_coverage(
        set_ids, plat_vecs, leak_vecs, radius,
    )
    reduced = tuple(
        a for a in set_ids if a != removed_id
    )
    new_cov = baseline_coverage(
        reduced, plat_vecs, leak_vecs, radius,
    )
    orphans = baseline - new_cov
    orphan_vecs = [leak_vecs[i] for i in orphans]
    if not orphan_vecs:
        return Localization(
            removed_id=removed_id, role=role,
            orphan_count=0, centroid=(),
            candidate_distances=(),
            predicted_id="", predicted_correct=False,
            hole_region_distance=float("inf"),
        )
    cent = _centroid(orphan_vecs)
    candidates = sorted(
        (
            (aid, _round(euclidean(cent, plat_vecs[aid])))
            for aid in set_ids
        ),
        key=lambda kv: kv[1],
    )
    predicted_id = candidates[0][0]
    return Localization(
        removed_id=removed_id, role=role,
        orphan_count=len(orphans),
        centroid=tuple(
            _round(c) for c in cent
        ),
        candidate_distances=tuple(candidates),
        predicted_id=predicted_id,
        predicted_correct=(
            predicted_id == removed_id
        ),
        hole_region_distance=_round(
            euclidean(
                cent, plat_vecs[removed_id],
            ),
        ),
    )


def all_localizations() -> tuple[
    Localization, ...,
]:
    plat_vecs, leak_vecs = _gather_vectors()
    set_ids = tuple(aid for aid, _ in TEST_CLAIM_SET)
    return tuple(
        localize_removal(
            aid, role, plat_vecs, leak_vecs,
            set_ids,
        )
        for aid, role in TEST_CLAIM_SET
    )


def localizable_count(
    locs: tuple[Localization, ...],
) -> int:
    return sum(1 for l in locs if l.orphan_count > 0)


def correct_localizations(
    locs: tuple[Localization, ...],
) -> int:
    return sum(
        1 for l in locs
        if l.orphan_count > 0
        and l.predicted_correct
    )


def localization_accuracy(
    locs: tuple[Localization, ...],
) -> float:
    n = localizable_count(locs)
    if n == 0:
        return 0.0
    return _round(correct_localizations(locs) / n)


def false_holes(
    locs: tuple[Localization, ...],
) -> int:
    """Localizations that point at a non-removed
    anchor. By construction, with one removal per
    iteration, false_holes counts incorrect top-1s."""
    return sum(
        1 for l in locs
        if l.orphan_count > 0
        and not l.predicted_correct
    )


def hole_region_distance_mean(
    locs: tuple[Localization, ...],
) -> float:
    eligible = [
        l.hole_region_distance for l in locs
        if l.orphan_count > 0
        and l.hole_region_distance != float("inf")
    ]
    if not eligible:
        return float("inf")
    return _round(sum(eligible) / len(eligible))


__all__ = [
    "Localization", "all_localizations",
    "correct_localizations", "false_holes",
    "hole_region_distance_mean",
    "localizable_count",
    "localization_accuracy", "localize_removal",
]
