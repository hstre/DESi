"""v3.31 — plateau metrics.

Pflichtmetriken (directive):

* ``plateau_count``             — trajectories whose
  final support_state == 2.0.
* ``plateau_terminal_rate``     — fraction of plateau
  trajectories whose plateau persists (terminal vs
  transient — by definition, all terminal plateaus have
  is_plateau == True so this rate is 1.0 over the
  plateau set; reported for traceability).
* ``plateau_replay_stability``  — fraction of plateau
  trajectories whose plateau membership is identical
  across two extractor runs.
* ``plateau_frequency``         — plateau_count / total
  trajectory count.
* ``plateau_outside_non_rescued`` — plateau trajectories
  NOT in the v3.30 non-rescued set.
"""
from __future__ import annotations

from dataclasses import dataclass

from .extractor import (
    census, non_rescued_ids, plateau_trajectory_ids,
)
from .state import PlateauObservation


@dataclass(frozen=True)
class PlateauMetrics:
    plateau_count: int
    plateau_terminal_rate: float
    plateau_replay_stability: float
    plateau_frequency: float
    plateau_outside_non_rescued: int
    non_rescued_outside_plateau: int

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "plateau_terminal_rate":
                self.plateau_terminal_rate,
            "plateau_replay_stability":
                self.plateau_replay_stability,
            "plateau_frequency": self.plateau_frequency,
            "plateau_outside_non_rescued":
                self.plateau_outside_non_rescued,
            "non_rescued_outside_plateau":
                self.non_rescued_outside_plateau,
        }


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def compute_metrics(
    observations: tuple[PlateauObservation, ...] | None = None,
) -> PlateauMetrics:
    obs = observations if observations is not None else census()
    total = len(obs)
    plateaus = [o for o in obs if o.is_plateau]
    plateau_count = len(plateaus)
    # By construction every is_plateau is terminal in
    # this corpus (the v3 extractor produces a single
    # audit state at s_{n-1}); reported as 1.0 when
    # plateau_count > 0.
    terminal = sum(1 for o in plateaus if o.is_plateau)
    terminal_rate = (
        _round(terminal / plateau_count)
        if plateau_count else 0.0
    )
    # Replay stability — re-run census and verify plateau
    # set identity.
    obs2 = census()
    set1 = {o.trajectory_id for o in plateaus}
    set2 = {
        o.trajectory_id for o in obs2 if o.is_plateau
    }
    matched = len(set1 & set2)
    union = len(set1 | set2)
    stability = (
        _round(matched / union) if union else 1.0
    )
    frequency = (
        _round(plateau_count / total) if total else 0.0
    )
    non_rescued = set(non_rescued_ids())
    plateau_outside = len(set1 - non_rescued)
    non_rescued_outside_plateau = len(non_rescued - set1)
    return PlateauMetrics(
        plateau_count=plateau_count,
        plateau_terminal_rate=terminal_rate,
        plateau_replay_stability=stability,
        plateau_frequency=frequency,
        plateau_outside_non_rescued=plateau_outside,
        non_rescued_outside_plateau=non_rescued_outside_plateau,
    )


__all__ = ["PlateauMetrics", "compute_metrics"]
