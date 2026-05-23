"""v3.71 — per-trajectory novelty axis classification.

Closed novelty taxonomy (matching directive § v3.71):

* ``semantic``       — driven by max-novelty axis
  (state.novelty)
* ``structural``    — driven by distinct frame
  count
* ``bridge``         — driven by BRIDGE_REQUIRED
  (support = 2.0) visits
* ``contradiction``  — driven by contradiction_load

Each trajectory gets a score per axis; a probe's
``coverage_source`` is the axis with the largest
absolute contribution after subtracting the corpus
median.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class NoveltyProfile:
    trajectory_id: str
    semantic: float
    structural: float
    bridge: float
    contradiction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "semantic": self.semantic,
            "structural": self.structural,
            "bridge": self.bridge,
            "contradiction": self.contradiction,
        }


def novelty_profile(traj: Trajectory) -> NoveltyProfile:
    states = traj.states
    if not states:
        return NoveltyProfile(
            trajectory_id=traj.trajectory_id,
            semantic=0.0, structural=0.0,
            bridge=0.0, contradiction=0.0,
        )
    semantic = max(s.novelty for s in states)
    structural = float(
        len(set(s.frame_id for s in states)),
    )
    bridge = float(
        sum(
            1 for s in states
            if s.support_state == 2.0
        ),
    )
    contradiction = max(
        s.contradiction_load for s in states
    )
    return NoveltyProfile(
        trajectory_id=traj.trajectory_id,
        semantic=_round(semantic),
        structural=_round(structural),
        bridge=_round(bridge),
        contradiction=_round(contradiction),
    )


def dominant_novelty_type(
    profile: NoveltyProfile,
) -> str:
    axes = {
        "semantic": profile.semantic / 10.0,
        "structural": profile.structural / 2.0,
        "bridge": profile.bridge,
        "contradiction": profile.contradiction,
    }
    if all(v == 0 for v in axes.values()):
        return "none"
    return max(
        axes.items(),
        key=lambda kv: (kv[1], kv[0]),
    )[0]


def all_novelty_profiles() -> tuple[
    NoveltyProfile, ...,
]:
    return tuple(
        novelty_profile(t)
        for t in extract_all_trajectories()
    )


__all__ = [
    "NoveltyProfile",
    "all_novelty_profiles",
    "dominant_novelty_type",
    "novelty_profile",
]
