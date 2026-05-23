"""v3.63 — per-anchor failure profile.

Closed set of failure features for each plateau
trajectory:

* ``primary_cause``         — v3.32 cause-class label
  (CONFIDENCE_OSCILLATION for every plateau in this
  corpus; included for completeness)
* ``source_corpus``         — normalised id prefix
* ``contradiction_load_at_final`` — final state's
  contradiction_load value (0.0 or 1.0)
* ``anchor_density_bucket`` — discretised
  anchor_density at the final state
* ``branch_cost_at_final``  — final state's
  branch_cost value
"""
from __future__ import annotations

from dataclasses import dataclass

from ..cross_corpus.corpus_loader import (
    normalised_prefix,
)
from ..epistemic_trajectory.extractor import (
    Trajectory,
)
from ..field_leakage.census import (
    collect_plateau_anchors,
)
from ..trajectory_root_cause.classifier import (
    classify_trajectory,
)


def _bucket_anchor_density(value: float) -> str:
    """Discretise into {none, sparse, dense} buckets
    so failure profiles don't depend on numerical
    jitter in the underlying density measurement."""
    if value == 0.0:
        return "none"
    if value < 0.10:
        return "sparse"
    return "dense"


@dataclass(frozen=True)
class FailureProfile:
    trajectory_id: str
    primary_cause: str
    source_corpus: str
    contradiction_load_at_final: float
    anchor_density_bucket: str
    branch_cost_at_final: float

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "primary_cause": self.primary_cause,
            "source_corpus": self.source_corpus,
            "contradiction_load_at_final":
                self.contradiction_load_at_final,
            "anchor_density_bucket":
                self.anchor_density_bucket,
            "branch_cost_at_final":
                self.branch_cost_at_final,
        }


def _make_profile(traj: Trajectory) -> FailureProfile:
    cls = classify_trajectory(traj)
    final = traj.states[-1]
    return FailureProfile(
        trajectory_id=traj.trajectory_id,
        primary_cause=cls.primary_cause,
        source_corpus=normalised_prefix(
            traj.trajectory_id,
        ),
        contradiction_load_at_final=(
            final.contradiction_load
        ),
        anchor_density_bucket=_bucket_anchor_density(
            final.anchor_density,
        ),
        branch_cost_at_final=final.branch_cost,
    )


def plateau_failure_profiles(
) -> tuple[FailureProfile, ...]:
    return tuple(
        _make_profile(t)
        for t in collect_plateau_anchors()
    )


__all__ = [
    "FailureProfile", "plateau_failure_profiles",
]
