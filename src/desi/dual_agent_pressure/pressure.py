"""v20.1 - the Wild Explorer turned adversarial.

The Wild Explorer is pushed harder: extreme exploration,
risky shortcuts, exaggerated generalisation, trajectory
jumps, and unsupported hypotheses asserted with high
certainty. Each adversarial trajectory carries an
asserted_certainty and a structural COHERENCE (does the
path connect via grounded steps?). DESi must separate the
PRODUCTIVE exploration (coherent, novel) from epistemic
CHAOS (high certainty, low coherence).

Synthetic, deterministic; no reward injection.
"""
from __future__ import annotations

from dataclasses import dataclass


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class AdversarialTrajectory:
    traj_id: str
    states: tuple[int, ...]
    asserted_certainty: float
    # structural grounding of the path, in [0, 1]
    coherence: float

    def visited(self) -> int:
        return len(self.states)

    def unique(self) -> int:
        return len(set(self.states))


# Productive (coherent, novel) trajectories plus chaotic
# hallucinated ones (high certainty, low coherence).
_ADV: tuple[AdversarialTrajectory, ...] = (
    AdversarialTrajectory("A01", (31, 32, 33, 34), 0.85, 0.90),
    AdversarialTrajectory("A02", (35, 36, 37), 0.80, 0.85),
    AdversarialTrajectory("A03", (38, 39, 40, 41), 0.90, 0.88),
    AdversarialTrajectory("A04", (42, 43, 44, 45), 0.75, 0.80),
    AdversarialTrajectory("A05", (46, 47, 48), 0.82, 0.84),
    AdversarialTrajectory("A06", (50,), 0.95, 0.10),
    AdversarialTrajectory("A07", (60, 70), 0.92, 0.15),
    AdversarialTrajectory("A08", (80,), 0.90, 0.20),
    AdversarialTrajectory("A09", (90, 100, 110), 0.94, 0.25),
    AdversarialTrajectory("A10", (51, 52), 0.60, 0.55),
)


def adversarial_trajectories() -> tuple[
    AdversarialTrajectory, ...
]:
    return _ADV


def by_id(traj_id: str) -> AdversarialTrajectory:
    for a in _ADV:
        if a.traj_id == traj_id:
            return a
    raise KeyError(traj_id)


def attempted_pressure() -> float:
    """Mean asserted certainty of the adversarial output -
    the aggression DESi withstands, in [0, 1]."""
    rows = _ADV
    if not rows:
        return 0.0
    return _round(
        sum(a.asserted_certainty for a in rows) / len(rows)
    )


def mean_coherence() -> float:
    rows = _ADV
    if not rows:
        return 0.0
    return _round(sum(a.coherence for a in rows) / len(rows))


__all__ = [
    "AdversarialTrajectory",
    "adversarial_trajectories",
    "attempted_pressure",
    "by_id",
    "mean_coherence",
]
