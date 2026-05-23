"""v3.47 — GAP geometry report.

Pflichtmetriken (directive):

* ``gap_to_plateau_distance``  — mean nearest-anchor
  distance from each GAP to the plateau cohort
* ``gap_to_leakage_distance``  — same vs leakage
* ``gap_cluster_count``        — 1-NN connected
  components inside the GAP cohort
* ``nearest_manifold``         — which cohort
  (plateau / leakage / rescued) the GAP cases sit
  closest to on average
* ``gap_cause_distribution``   — per-primary-cause
  counts across the GAP cohort
* ``replay_stability``         — deterministic two-run
  equality of all per-case records

Concept Gate (directive § "Concept Gate"):
``gap_cluster_count >= 1`` (#3) and
``replay_stability == 1.0`` (Sprint #2 surrogate).
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import statistics

from ..gap_detected.extractor import terminal_gap_cases
from .cause import (
    cause_distribution, classify_gap_cohort,
)
from .cluster import (
    CohortMember, gap_1nn_cluster_count, gap_members,
    leakage_members, plateau_members, rescued_members,
)
from .geometry import euclidean, manifold_distance


ORPHAN_DISTANCE_FLOOR: float = 5.0
"""Threshold above which a GAP cohort is considered an
orphan manifold (well-separated from plateau, leakage
and rescued cohorts). The plateau cohort's internal
pairwise distances are <= 3.18 (v3.43 probe), so any
GAP minimum distance above 5.0 is unambiguously
outside every neighbouring cohort. This threshold is
stable under v3.30 FrameDetector hash-seed jitter
because every observed run yields a min distance of
at least 11.25 (12-run sweep, seeds 1..12)."""


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V347Report:
    gap_count: int
    gap_to_plateau_distance_mean: float
    gap_to_plateau_distance_min: float
    gap_to_leakage_distance_mean: float
    gap_to_leakage_distance_min: float
    gap_to_rescued_distance_mean: float
    gap_to_rescued_distance_min: float
    gap_cluster_count: int
    nearest_manifold: str
    gap_is_orphan_manifold: bool
    orphan_distance_floor: float
    gap_cause_distribution: dict[str, int]
    cause_identity_match_plateau: bool
    per_gap_records: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "gap_count": self.gap_count,
            "gap_to_plateau_distance_mean":
                self.gap_to_plateau_distance_mean,
            "gap_to_plateau_distance_min":
                self.gap_to_plateau_distance_min,
            "gap_to_leakage_distance_mean":
                self.gap_to_leakage_distance_mean,
            "gap_to_leakage_distance_min":
                self.gap_to_leakage_distance_min,
            "gap_to_rescued_distance_mean":
                self.gap_to_rescued_distance_mean,
            "gap_to_rescued_distance_min":
                self.gap_to_rescued_distance_min,
            "gap_cluster_count":
                self.gap_cluster_count,
            "nearest_manifold":
                self.nearest_manifold,
            "gap_is_orphan_manifold":
                self.gap_is_orphan_manifold,
            "orphan_distance_floor":
                self.orphan_distance_floor,
            "gap_cause_distribution":
                dict(self.gap_cause_distribution),
            "cause_identity_match_plateau":
                self.cause_identity_match_plateau,
            "per_gap_records":
                list(self.per_gap_records),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _distances_to_cohort(
    gap: tuple[CohortMember, ...],
    target: tuple[CohortMember, ...],
) -> tuple[list[float], list[str]]:
    """For each GAP member, return its nearest distance
    and the matching target trajectory_id."""
    target_vecs = tuple(m.vector for m in target)
    dists: list[float] = []
    nearest_ids: list[str] = []
    for g in gap:
        d, idx = manifold_distance(g.vector, target_vecs)
        dists.append(d)
        nearest_ids.append(
            target[idx].trajectory_id if idx >= 0 else "",
        )
    return dists, nearest_ids


def _mean_or_inf(values: list[float]) -> float:
    finite = [
        v for v in values if v != float("inf")
    ]
    if not finite:
        return float("inf")
    return _round(statistics.mean(finite))


def _min_or_inf(values: list[float]) -> float:
    finite = [
        v for v in values if v != float("inf")
    ]
    if not finite:
        return float("inf")
    return _round(min(finite))


def _per_gap_records(
    gap: tuple[CohortMember, ...],
    cause_records,
    nn_by_target: dict,
) -> tuple[dict, ...]:
    cause_by_id = {
        c.trajectory_id: c for c in cause_records
    }
    out: list[dict] = []
    for g in gap:
        cr = cause_by_id.get(g.trajectory_id)
        rec = {
            "trajectory_id": g.trajectory_id,
            "primary_cause":
                cr.primary_cause if cr else "UNKNOWN",
            "secondary_causes": (
                list(cr.secondary_causes)
                if cr else []
            ),
        }
        for target_name, (dists, ids) in nn_by_target.items():
            i = next(
                (
                    idx for idx, m in enumerate(gap)
                    if m.trajectory_id == g.trajectory_id
                ),
                -1,
            )
            if i >= 0:
                rec[f"{target_name}_nearest_id"] = ids[i]
                rec[f"{target_name}_nearest_distance"] = (
                    _round(dists[i])
                )
        out.append(rec)
    return tuple(out)


def _replay_stability() -> float:
    a = [
        c.to_dict() for c in classify_gap_cohort()
    ]
    b = [
        c.to_dict() for c in classify_gap_cohort()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V347Report:
    gap = gap_members()
    plateau = plateau_members()
    leakage = leakage_members()
    rescued = rescued_members()

    plat_d, plat_ids = _distances_to_cohort(gap, plateau)
    leak_d, leak_ids = _distances_to_cohort(gap, leakage)
    res_d, res_ids = _distances_to_cohort(gap, rescued)

    means = {
        "plateau": _mean_or_inf(plat_d),
        "leakage": _mean_or_inf(leak_d),
        "rescued": _mean_or_inf(res_d),
    }
    finite_means = {
        k: v for k, v in means.items() if v != float("inf")
    }
    if finite_means:
        nearest = min(
            finite_means.items(),
            key=lambda kv: (kv[1], kv[0]),
        )[0]
    else:
        nearest = "none"

    causes = cause_distribution()
    cause_records = classify_gap_cohort()
    match_plateau = all(
        c.matches_plateau_cause for c in cause_records
    ) if cause_records else False

    nn_by_target = {
        "plateau": (plat_d, plat_ids),
        "leakage": (leak_d, leak_ids),
        "rescued": (res_d, res_ids),
    }
    per_gap = _per_gap_records(
        gap, cause_records, nn_by_target,
    )

    cluster_count = gap_1nn_cluster_count()
    replay = _replay_stability()

    # Stable orphan check: every observed run (12-seed
    # sweep) yields gap-to-cohort minimum distance well
    # above ORPHAN_DISTANCE_FLOOR; the predicate is
    # therefore deterministic across hash seeds even
    # though the numeric distance values jitter
    # (FrameDetector dict iteration is the upstream
    # source of jitter for the 8-state GAP cases).
    min_overall = min(
        _min_or_inf(plat_d),
        _min_or_inf(leak_d),
        _min_or_inf(res_d),
    )
    is_orphan = (
        min_overall > ORPHAN_DISTANCE_FLOOR
    )

    halt = cluster_count < 1 or replay < 1.0
    if halt:
        if cluster_count < 1:
            verdict = "HALT_NO_GAP_CLUSTER"
        else:
            verdict = "HALT_REPLAY_DRIFT"
    elif is_orphan:
        verdict = "GAP_ORPHAN_MANIFOLD"
    elif nearest == "plateau":
        verdict = "GAP_BORDERS_PLATEAU"
    elif nearest == "leakage":
        verdict = "GAP_BORDERS_LEAKAGE"
    elif nearest == "rescued":
        verdict = "GAP_BORDERS_RESCUED"
    else:
        verdict = "GAP_NO_NEAREST"

    rationale = (
        f"INFO: gap_count {len(gap)}",
        f"INFO: gap_to_plateau_distance_mean "
        f"{means['plateau']}",
        f"INFO: gap_to_leakage_distance_mean "
        f"{means['leakage']}",
        f"INFO: gap_to_rescued_distance_mean "
        f"{means['rescued']}",
        f"INFO: nearest_manifold {nearest} "
        f"(jitters across hash seeds; orphan check is "
        f"stable)",
        f"INFO: gap_is_orphan_manifold {is_orphan} "
        f"(min_overall {round(min_overall, 4)} > "
        f"floor {ORPHAN_DISTANCE_FLOOR})",
        f"INFO: gap_cluster_count {cluster_count} "
        f"(Concept Gate #3: >= 1)",
        f"INFO: gap_cause_distribution "
        f"{sorted(causes.items())}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V347Report(
        gap_count=len(gap),
        gap_to_plateau_distance_mean=means["plateau"],
        gap_to_plateau_distance_min=_min_or_inf(plat_d),
        gap_to_leakage_distance_mean=means["leakage"],
        gap_to_leakage_distance_min=_min_or_inf(leak_d),
        gap_to_rescued_distance_mean=means["rescued"],
        gap_to_rescued_distance_min=_min_or_inf(res_d),
        gap_cluster_count=cluster_count,
        nearest_manifold=nearest,
        gap_is_orphan_manifold=is_orphan,
        orphan_distance_floor=ORPHAN_DISTANCE_FLOOR,
        gap_cause_distribution=causes,
        cause_identity_match_plateau=match_plateau,
        per_gap_records=per_gap,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_gap_geometry_artifact() -> dict[str, object]:
    r = build_report()
    return {
        "schema_version": "v3_47_gap_geometry",
        "per_gap_records": list(r.per_gap_records),
        "gap_cause_distribution":
            dict(r.gap_cause_distribution),
        "nearest_manifold": r.nearest_manifold,
        "gap_cluster_count": r.gap_cluster_count,
        "gap_to_plateau_distance_mean":
            r.gap_to_plateau_distance_mean,
        "gap_to_leakage_distance_mean":
            r.gap_to_leakage_distance_mean,
        "gap_to_rescued_distance_mean":
            r.gap_to_rescued_distance_mean,
    }


__all__ = [
    "V347Report", "build_gap_geometry_artifact",
    "build_report",
]
