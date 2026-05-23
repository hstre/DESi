"""v3.36 — confidence noise robustness.

For each plateau trajectory and each noise level
(-20%, -10%, -5%, +5%, +10%, +20%), scale the
confidence dimension at every state by ``(1 + noise)``
and simulate a re-audit by a closed rule:

* ``max(confidence) >= 0.5``       → SUPPORTED  (4.0)
* ``max(confidence) <  0.10``      → REJECTED   (3.0)
* otherwise                        → BRIDGE_REQUIRED (2.0)

The plateau is *noise-stable* on a trajectory if every
noise level keeps the simulated verdict at 2.0.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import Trajectory
from ..epistemic_trajectory.state import StateVector


_BRIDGE_REQUIRED = 2.0
_REJECTED        = 3.0
_SUPPORTED       = 4.0
_REAUDIT_HIGH    = 0.5
_REAUDIT_LOW     = 0.10


NOISE_LEVELS: tuple[float, ...] = (
    -0.20, -0.10, -0.05, 0.05, 0.10, 0.20,
)


def _replace(s: StateVector, **u) -> StateVector:
    d = s.to_dict()
    d.update(u)
    return StateVector(**d)


def apply_noise(
    states: tuple[StateVector, ...], noise: float,
) -> tuple[StateVector, ...]:
    out: list[StateVector] = []
    for s in states:
        new_conf = max(0.0, s.confidence * (1.0 + noise))
        out.append(_replace(s, confidence=new_conf))
    return tuple(out)


def simulate_reaudit(
    states: tuple[StateVector, ...],
) -> float:
    if not states:
        return _BRIDGE_REQUIRED
    max_conf = max(s.confidence for s in states)
    if max_conf >= _REAUDIT_HIGH:
        return _SUPPORTED
    if max_conf < _REAUDIT_LOW:
        return _REJECTED
    return _BRIDGE_REQUIRED


@dataclass(frozen=True)
class NoiseOutcome:
    trajectory_id: str
    noise_pct: float
    original_max_confidence: float
    noisy_max_confidence: float
    original_final_support: float
    simulated_final_support: float
    plateau_held: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "noise_pct": self.noise_pct,
            "original_max_confidence":
                self.original_max_confidence,
            "noisy_max_confidence":
                self.noisy_max_confidence,
            "original_final_support":
                self.original_final_support,
            "simulated_final_support":
                self.simulated_final_support,
            "plateau_held": self.plateau_held,
        }


def run_noise_level(
    traj: Trajectory, noise: float,
) -> NoiseOutcome:
    noisy = apply_noise(traj.states, noise)
    new_final = simulate_reaudit(noisy)
    orig_max = max(s.confidence for s in traj.states)
    new_max = max(s.confidence for s in noisy)
    held = (
        traj.states[-1].support_state == _BRIDGE_REQUIRED
        and new_final == _BRIDGE_REQUIRED
    )
    return NoiseOutcome(
        trajectory_id=traj.trajectory_id,
        noise_pct=noise,
        original_max_confidence=round(orig_max, 6),
        noisy_max_confidence=round(new_max, 6),
        original_final_support=(
            traj.states[-1].support_state
        ),
        simulated_final_support=new_final,
        plateau_held=held,
    )


def all_noise_outcomes(
    trajectories: tuple[Trajectory, ...],
) -> tuple[NoiseOutcome, ...]:
    out: list[NoiseOutcome] = []
    for t in trajectories:
        for n in NOISE_LEVELS:
            out.append(run_noise_level(t, n))
    return tuple(out)


__all__ = [
    "NOISE_LEVELS", "NoiseOutcome", "all_noise_outcomes",
    "apply_noise", "run_noise_level", "simulate_reaudit",
]
