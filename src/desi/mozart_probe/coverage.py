"""v3.69 — historical probe coverage reconstruction.

Defines per-trajectory richness metrics for the three
sample-corpus probes the directive names
(sample:n03_mozart, sample:n03_darwin,
sample:n03_kant). Missing probes are reported but
NOT substituted.

The coverage_score is a closed-form composite of:

* ``distinct_frames``      — count of unique frame_id
  values visited
* ``novelty_range``        — max(novelty) - min(novelty)
* ``anchor_density_range`` — max(ad) - min(ad)

    coverage_score = distinct_frames *
        (1 + anchor_density_range) *
        (1 + novelty_range / 10)
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)


HISTORICAL_PROBES: tuple[str, ...] = (
    "sample:n03_mozart",
    "sample:n03_darwin",
    "sample:n03_kant",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ProbeCoverage:
    trajectory_id: str
    trajectory_length: int
    distinct_frames: int
    novelty_range: float
    anchor_density_range: float
    bridge_events: int
    gap_events: int
    coverage_score: float
    available: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "trajectory_length":
                self.trajectory_length,
            "distinct_frames": self.distinct_frames,
            "novelty_range": self.novelty_range,
            "anchor_density_range":
                self.anchor_density_range,
            "bridge_events": self.bridge_events,
            "gap_events": self.gap_events,
            "coverage_score": self.coverage_score,
            "available": self.available,
        }


def _missing_coverage(tid: str) -> ProbeCoverage:
    return ProbeCoverage(
        trajectory_id=tid, trajectory_length=0,
        distinct_frames=0, novelty_range=0.0,
        anchor_density_range=0.0,
        bridge_events=0, gap_events=0,
        coverage_score=0.0, available=False,
    )


def _coverage_for(traj: Trajectory) -> ProbeCoverage:
    states = traj.states
    distinct_frames = len(
        set(s.frame_id for s in states)
    )
    novelty_max = max(s.novelty for s in states)
    novelty_min = min(s.novelty for s in states)
    novelty_range = novelty_max - novelty_min
    ad_max = max(s.anchor_density for s in states)
    ad_min = min(s.anchor_density for s in states)
    ad_range = ad_max - ad_min
    bridge_events = sum(
        1 for s in states if s.support_state == 2.0
    )
    gap_events = sum(
        1 for s in states if s.support_state == 1.0
    )
    score = _round(
        distinct_frames
        * (1.0 + ad_range)
        * (1.0 + novelty_range / 10.0),
    )
    return ProbeCoverage(
        trajectory_id=traj.trajectory_id,
        trajectory_length=len(states),
        distinct_frames=distinct_frames,
        novelty_range=_round(novelty_range),
        anchor_density_range=_round(ad_range),
        bridge_events=bridge_events,
        gap_events=gap_events,
        coverage_score=score, available=True,
    )


def all_coverages() -> tuple[ProbeCoverage, ...]:
    return tuple(
        _coverage_for(t)
        for t in extract_all_trajectories()
    )


def probe_coverage(tid: str) -> ProbeCoverage:
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    t = trajs.get(tid)
    if t is None:
        return _missing_coverage(tid)
    return _coverage_for(t)


def historical_coverages() -> tuple[
    ProbeCoverage, ...,
]:
    return tuple(
        probe_coverage(p) for p in HISTORICAL_PROBES
    )


def coverage_percentile(
    target: ProbeCoverage,
    population: tuple[ProbeCoverage, ...],
) -> float:
    """Fraction of population trajectories whose
    coverage_score is strictly LESS than the target's.
    1.0 means the target is the strict maximum."""
    if not target.available:
        return 0.0
    scores = [
        c.coverage_score for c in population
        if c.trajectory_id != target.trajectory_id
    ]
    if not scores:
        return 0.0
    below = sum(
        1 for s in scores
        if s < target.coverage_score
    )
    return _round(below / len(scores))


__all__ = [
    "HISTORICAL_PROBES", "ProbeCoverage",
    "all_coverages", "coverage_percentile",
    "historical_coverages", "probe_coverage",
]
