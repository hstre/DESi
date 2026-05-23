"""v3.28 — root-cause observer report.

Pflichtmetriken (directive):

* ``classified_cliffs`` — count of cliff-bearing
  trajectories with a non-UNKNOWN cause.
* ``unknown_rate``      — UNKNOWN / cliff_count.
* ``cause_distribution`` — per-class counts over the
  cliff set.
* ``multi_cause_rate``  — fraction of classified cliffs
  carrying ≥ 1 secondary cause.
* ``replay_stability``  — fraction of trajectories
  whose primary cause is identical across two runs (must
  be 1.0 on the deterministic classifier).

Stop rule: ``cause_nc_fp > 0.10`` triggers HALT.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..trajectory_control.negative_controls import all_ncs
from .cause import CauseClass
from .classifier import (
    CauseAssignment, classify_all, classify_trajectory,
)


# Gates
MAX_UNKNOWN_RATE              = 0.20
MAX_CAUSE_NC_FP_RATE          = 0.10
MIN_REPLAY_STABILITY          = 1.0


@dataclass(frozen=True)
class V328Report:
    trajectory_count: int
    cliff_count: int
    classified_cliffs: int
    unknown_rate: float
    cause_distribution: dict[str, int]
    multi_cause_rate: float
    replay_stability: float
    nc_count: int
    cause_nc_fp_rate: float
    per_nc_kind_fp_rate: dict[str, float]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "cliff_count": self.cliff_count,
            "classified_cliffs": self.classified_cliffs,
            "unknown_rate": self.unknown_rate,
            "cause_distribution":
                dict(self.cause_distribution),
            "multi_cause_rate": self.multi_cause_rate,
            "replay_stability": self.replay_stability,
            "nc_count": self.nc_count,
            "cause_nc_fp_rate": self.cause_nc_fp_rate,
            "per_nc_kind_fp_rate":
                dict(self.per_nc_kind_fp_rate),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def build_report() -> V328Report:
    trajs = extract_all_trajectories()
    assignments = classify_all(trajs)
    cliff_assignments = [
        a for a in assignments if a.has_cliff
    ]
    cliff_count = len(cliff_assignments)
    classified = sum(
        1 for a in cliff_assignments
        if a.primary_cause != CauseClass.UNKNOWN.value
    )
    unknown_rate = (
        _round((cliff_count - classified) / cliff_count)
        if cliff_count else 0.0
    )

    dist: Counter = Counter()
    for a in cliff_assignments:
        dist[a.primary_cause] += 1
    multi = sum(
        1 for a in cliff_assignments
        if a.secondary_causes
        and a.primary_cause != CauseClass.UNKNOWN.value
    )
    multi_rate = (
        _round(multi / classified) if classified else 0.0
    )

    # Replay stability — primary cause identical across
    # two runs.
    a1 = classify_all(trajs)
    a2 = classify_all(trajs)
    matches = sum(
        1 for x, y in zip(a1, a2)
        if x.primary_cause == y.primary_cause
        and x.trajectory_id == y.trajectory_id
    )
    replay_stab = (
        _round(matches / len(a1)) if a1 else 0.0
    )

    # NC false-positive rate (any non-UNKNOWN on NCs).
    ncs = all_ncs()
    nc_assigns = [
        classify_trajectory(n.trajectory) for n in ncs
    ]
    nc_fp = sum(
        1 for a in nc_assigns
        if a.primary_cause != CauseClass.UNKNOWN.value
    )
    nc_fp_rate = (
        _round(nc_fp / len(ncs)) if ncs else 0.0
    )
    per_kind_total: Counter = Counter()
    per_kind_fp: Counter = Counter()
    for nc, a in zip(ncs, nc_assigns):
        per_kind_total[nc.kind] += 1
        if a.primary_cause != CauseClass.UNKNOWN.value:
            per_kind_fp[nc.kind] += 1
    per_kind = {
        k: _round(per_kind_fp[k] / per_kind_total[k])
        for k in per_kind_total
    }

    halt = nc_fp_rate > MAX_CAUSE_NC_FP_RATE
    if halt:
        verdict = "HALT_CAUSE_NC_FP"
    elif unknown_rate <= MAX_UNKNOWN_RATE and \
            replay_stab >= MIN_REPLAY_STABILITY:
        verdict = "ROOT_CAUSE_OBSERVER_READY"
    else:
        verdict = "ROOT_CAUSE_OBSERVER_PARTIAL"

    rationale = (
        f"{'PASS' if unknown_rate <= MAX_UNKNOWN_RATE else 'FAIL'}: "
        f"unknown_rate {unknown_rate} <= {MAX_UNKNOWN_RATE}",
        f"{'PASS' if not halt else 'FAIL'}: "
        f"cause_nc_fp_rate {nc_fp_rate} <= "
        f"{MAX_CAUSE_NC_FP_RATE}",
        f"{'PASS' if replay_stab >= MIN_REPLAY_STABILITY else 'FAIL'}: "
        f"replay_stability {replay_stab} >= "
        f"{MIN_REPLAY_STABILITY}",
    )

    return V328Report(
        trajectory_count=len(trajs),
        cliff_count=cliff_count,
        classified_cliffs=classified,
        unknown_rate=unknown_rate,
        cause_distribution=dict(dist),
        multi_cause_rate=multi_rate,
        replay_stability=replay_stab,
        nc_count=len(ncs),
        cause_nc_fp_rate=nc_fp_rate,
        per_nc_kind_fp_rate=per_kind,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_taxonomy_artifact() -> dict[str, object]:
    return {
        "schema_version": "v3_28_root_cause_taxonomy",
        "classes": [
            {
                "name": CauseClass.SUPPORT_DECAY.value,
                "description":
                    "Trajectory's support_state eroded "
                    "across multiple transitions before "
                    "the final audit.",
            },
            {
                "name": CauseClass.FRAME_COLLISION.value,
                "description":
                    "Frame_id changed mid-trajectory; "
                    "the audit step inherited a "
                    "frame-shifted context.",
            },
            {
                "name": CauseClass.BRANCH_OVERLOAD.value,
                "description":
                    "Branch_cost grew above baseline; "
                    "too many active premises by the "
                    "audit step.",
            },
            {
                "name": CauseClass.CAUSAL_LEAP.value,
                "description":
                    "Final-state novelty spike "
                    "indicating premises don't span "
                    "the conclusion's vocabulary.",
            },
            {
                "name":
                    CauseClass.CONFIDENCE_OSCILLATION.value,
                "description":
                    "Confidence oscillated across "
                    "states; final commit lacked a "
                    "stable confidence anchor.",
            },
            {
                "name": CauseClass.UNKNOWN.value,
                "description":
                    "No signal exceeds its threshold; "
                    "forced classification forbidden.",
            },
        ],
    }


def build_distribution_artifact() -> dict[str, object]:
    trajs = extract_all_trajectories()
    assignments = classify_all(trajs)
    return {
        "schema_version": "v3_28_cliff_cause_distribution",
        "assignments": [
            a.to_dict() for a in assignments if a.has_cliff
        ],
    }


__all__ = [
    "MAX_CAUSE_NC_FP_RATE", "MAX_UNKNOWN_RATE",
    "MIN_REPLAY_STABILITY", "V328Report",
    "build_distribution_artifact", "build_report",
    "build_taxonomy_artifact",
]
