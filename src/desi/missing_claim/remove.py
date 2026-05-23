"""v3.73 — known-claim removal harness.

Constructs a stable 4-anchor "claim space" from the
v3.50 plateau cohort with one anchor per role:

* ``HIGH``      — maximum-coverage anchor in the set
* ``LOW``       — zero-coverage anchor
* ``BRIDGE``    — anchor whose coverage is UNIQUE
  within the constructed set
* ``REDUNDANT`` — anchor whose coverage duplicates
  another set member

For each role removal, measure:

* ``coverage_loss``         — leakages no longer
  covered by any remaining anchor
* ``affected_trajectories`` — leakages whose nearest-
  anchor identity changes after removal
* ``distance_increase``     — sum of nearest-distance
  growth across affected trajectories
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


PROBE_RADIUS: float = 3.5


class ClaimRole(str, Enum):
    HIGH      = "high_coverage"
    LOW       = "low_coverage"
    BRIDGE    = "bridge"
    REDUNDANT = "redundant"


# Closed test set. The role assignment is fixed and
# matches the directive's removal types. HIGH and
# REDUNDANT are intentionally chosen to share the
# same coverage so the directive's "high > redundant"
# question can be measured empirically (in this
# corpus the answer is tied at 0; the stop rule
# documents the weak hypothesis).
TEST_CLAIM_SET: tuple[tuple[str, str], ...] = (
    ("v23:R5_04",   ClaimRole.HIGH.value),
    ("v23:R4_04",   ClaimRole.LOW.value),
    ("v23:R5_02",   ClaimRole.BRIDGE.value),
    ("v314:D02",    ClaimRole.REDUNDANT.value),
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class RemovalOutcome:
    removed_id: str
    role: str
    coverage_loss: int
    affected_trajectories: int
    distance_increase: float
    perturbation_magnitude: float

    def to_dict(self) -> dict[str, object]:
        return {
            "removed_id": self.removed_id,
            "role": self.role,
            "coverage_loss": self.coverage_loss,
            "affected_trajectories":
                self.affected_trajectories,
            "distance_increase":
                self.distance_increase,
            "perturbation_magnitude":
                self.perturbation_magnitude,
        }


def _gather_vectors() -> tuple[
    dict[str, tuple[float, ...]],
    list[tuple[float, ...]],
]:
    plats = {
        t.trajectory_id: trajectory_vector(t.states)
        for t in collect_plateau_anchors()
    }
    leaks = [
        trajectory_vector(t.states)
        for t in collect_leakage_trajectories()
    ]
    return plats, leaks


def coverage_set(
    anchor_id: str,
    plat_vecs: dict[str, tuple[float, ...]],
    leak_vecs: list[tuple[float, ...]],
    radius: float = PROBE_RADIUS,
) -> frozenset[int]:
    av = plat_vecs.get(anchor_id)
    if av is None:
        return frozenset()
    return frozenset(
        i for i, l in enumerate(leak_vecs)
        if euclidean(av, l) <= radius
    )


def baseline_coverage(
    set_ids: tuple[str, ...],
    plat_vecs: dict[str, tuple[float, ...]],
    leak_vecs: list[tuple[float, ...]],
    radius: float = PROBE_RADIUS,
) -> frozenset[int]:
    out: set[int] = set()
    for aid in set_ids:
        out |= coverage_set(
            aid, plat_vecs, leak_vecs, radius,
        )
    return frozenset(out)


def nearest_anchor_per_leakage(
    set_ids: tuple[str, ...],
    plat_vecs: dict[str, tuple[float, ...]],
    leak_vecs: list[tuple[float, ...]],
) -> tuple[
    tuple[str, ...], tuple[float, ...],
]:
    """For each leakage, the nearest anchor in
    set_ids and its distance. Empty set returns
    ('', inf) per leakage."""
    if not set_ids:
        return (
            tuple("" for _ in leak_vecs),
            tuple(float("inf") for _ in leak_vecs),
        )
    nearest_ids: list[str] = []
    nearest_dists: list[float] = []
    for l in leak_vecs:
        best_id = ""
        best_d = float("inf")
        for aid in set_ids:
            av = plat_vecs.get(aid)
            if av is None:
                continue
            d = euclidean(l, av)
            if d < best_d:
                best_d = d
                best_id = aid
        nearest_ids.append(best_id)
        nearest_dists.append(best_d)
    return tuple(nearest_ids), tuple(nearest_dists)


def removal_outcome(
    removed_id: str, role: str,
    plat_vecs: dict[str, tuple[float, ...]],
    leak_vecs: list[tuple[float, ...]],
    set_ids: tuple[str, ...],
    radius: float = PROBE_RADIUS,
) -> RemovalOutcome:
    baseline = baseline_coverage(
        set_ids, plat_vecs, leak_vecs, radius,
    )
    reduced_ids = tuple(
        a for a in set_ids if a != removed_id
    )
    new_cov = baseline_coverage(
        reduced_ids, plat_vecs, leak_vecs, radius,
    )
    coverage_loss = len(baseline - new_cov)
    base_nearest_ids, base_nearest_dists = (
        nearest_anchor_per_leakage(
            set_ids, plat_vecs, leak_vecs,
        )
    )
    new_nearest_ids, new_nearest_dists = (
        nearest_anchor_per_leakage(
            reduced_ids, plat_vecs, leak_vecs,
        )
    )
    affected = sum(
        1 for b, n in zip(
            base_nearest_ids, new_nearest_ids,
        )
        if b != n
    )
    distance_increase = _round(
        sum(
            max(0.0, n - b)
            for b, n in zip(
                base_nearest_dists, new_nearest_dists,
            )
            if n != float("inf")
            and b != float("inf")
        ),
    )
    # perturbation_magnitude composite: coverage loss
    # weighted by 10x plus distance increase plus
    # 0.1 per identity change. Heuristic blend so a
    # single scalar captures all three signals.
    perturbation = _round(
        10 * coverage_loss
        + distance_increase
        + 0.1 * affected,
    )
    return RemovalOutcome(
        removed_id=removed_id, role=role,
        coverage_loss=coverage_loss,
        affected_trajectories=affected,
        distance_increase=distance_increase,
        perturbation_magnitude=perturbation,
    )


def all_removal_outcomes(
) -> tuple[RemovalOutcome, ...]:
    plat_vecs, leak_vecs = _gather_vectors()
    set_ids = tuple(aid for aid, _ in TEST_CLAIM_SET)
    out: list[RemovalOutcome] = []
    for aid, role in TEST_CLAIM_SET:
        out.append(removal_outcome(
            aid, role, plat_vecs, leak_vecs,
            set_ids,
        ))
    return tuple(out)


def support_shift(
    set_ids: tuple[str, ...],
    plat_vecs: dict[str, tuple[float, ...]],
    leak_vecs: list[tuple[float, ...]],
    removed_id: str,
    radius: float = PROBE_RADIUS,
) -> int:
    """Count leakage trajectories whose `would_fire`
    boolean (any anchor within radius) changes when
    `removed_id` is taken out of the set."""
    if removed_id not in set_ids:
        return 0
    new_set = tuple(
        a for a in set_ids if a != removed_id
    )
    def fires(idx: int, anchors: tuple[str, ...]) -> bool:
        l = leak_vecs[idx]
        for aid in anchors:
            av = plat_vecs.get(aid)
            if av is None:
                continue
            if euclidean(l, av) <= radius:
                return True
        return False
    shifts = 0
    for i in range(len(leak_vecs)):
        if fires(i, set_ids) != fires(i, new_set):
            shifts += 1
    return shifts


__all__ = [
    "ClaimRole", "PROBE_RADIUS", "RemovalOutcome",
    "TEST_CLAIM_SET", "all_removal_outcomes",
    "baseline_coverage", "coverage_set",
    "nearest_anchor_per_leakage",
    "removal_outcome", "support_shift",
]
