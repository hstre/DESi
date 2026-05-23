"""Aufgabe 5 — synthetic negative-control trajectories.

Fifty trajectories synthesised as state-vector sequences (not
fed through the real pipeline). Each carries an expected
``anomalous`` label so the detector can be scored:

* ``smooth_but_false``      — small smooth ΔV; expected NOT
  anomalous (smoothness is form, not truth).
* ``jagged_but_valid``      — large ΔV; expected anomalous on
  smoothness/jerk *despite* being valid.
* ``frame_flipping``        — flips ``frame_id`` between states.
* ``contradiction_spiking`` — spikes ``contradiction_load``
  mid-trajectory.
* ``marker_free_non_sequitur`` — all features near zero;
  expected NOT anomalous (the hard limit; mirrors v3.18's WMF
  finding).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .state import StateVector, TrajectorySource


class NCShape(str, Enum):
    SMOOTH_BUT_FALSE        = "smooth_but_false"
    JAGGED_BUT_VALID        = "jagged_but_valid"
    FRAME_FLIPPING          = "frame_flipping"
    CONTRADICTION_SPIKING   = "contradiction_spiking"
    MARKER_FREE_NON_SEQUITUR = "marker_free_non_sequitur"


@dataclass(frozen=True)
class NCTrajectory:
    case_id: str
    shape: NCShape
    states: tuple[StateVector, ...]
    expected_anomalous: bool


def _v(frame_id: float, contradiction: float, anchor: float,
       source_q: float, novelty: float, conf: float,
       branch: float, sup: float, route: float) -> StateVector:
    return StateVector(
        frame_id=frame_id, contradiction_load=contradiction,
        anchor_density=anchor, source_quality=source_q,
        novelty=novelty, confidence=conf,
        branch_cost=branch, support_state=sup, routing_state=route,
    )


def _smooth_but_false(idx: int) -> NCTrajectory:
    # Geometrically smooth: frame, support, routing all hold
    # constant; only confidence grows mildly. Trajectory is not
    # anomalous on form even though the underlying claim could
    # be false — naturalness is about distribution, not truth.
    states = tuple(
        _v(2.0, 0.0, 0.05, 0.0, 0.1,
           0.2 + 0.15 * i, 2.0, 4.0, 2.0)
        for i in range(5)
    )
    return NCTrajectory(
        case_id=f"SBF{idx:02d}", shape=NCShape.SMOOTH_BUT_FALSE,
        states=states, expected_anomalous=False,
    )


def _jagged_but_valid(idx: int) -> NCTrajectory:
    # Large oscillations in confidence/novelty.
    pattern = ((0.1, 0.0), (0.9, 5.0), (0.2, 0.1),
               (0.8, 4.0), (1.0, 0.5))
    states = tuple(
        _v(2.0, 0.0, 0.0, 0.0, novelty, conf, 2.0, 4.0, 2.0)
        for conf, novelty in pattern
    )
    return NCTrajectory(
        case_id=f"JBV{idx:02d}", shape=NCShape.JAGGED_BUT_VALID,
        states=states, expected_anomalous=True,
    )


def _frame_flipping(idx: int) -> NCTrajectory:
    flips = (1.0, 4.0, 7.0, 2.0, 5.0)
    states = tuple(
        _v(f, 0.0, 0.0, 0.0, 1.0, 0.5, 2.0, 2.0, 2.0)
        for f in flips
    )
    return NCTrajectory(
        case_id=f"FF{idx:02d}", shape=NCShape.FRAME_FLIPPING,
        states=states, expected_anomalous=True,
    )


def _contradiction_spiking(idx: int) -> NCTrajectory:
    contradictions = (0.0, 0.0, 3.0, 0.0, 0.0)
    states = tuple(
        _v(2.0, c, 0.0, 0.0, 0.5, 0.5, 2.0, 1.0, 2.0)
        for c in contradictions
    )
    return NCTrajectory(
        case_id=f"CS{idx:02d}",
        shape=NCShape.CONTRADICTION_SPIKING,
        states=states, expected_anomalous=True,
    )


def _marker_free_non_sequitur(idx: int) -> NCTrajectory:
    states = tuple(
        _v(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0)
        for _ in range(5)
    )
    return NCTrajectory(
        case_id=f"WMF{idx:02d}",
        shape=NCShape.MARKER_FREE_NON_SEQUITUR,
        states=states, expected_anomalous=False,
    )


def _build_all() -> tuple[NCTrajectory, ...]:
    out: list[NCTrajectory] = []
    for i in range(1, 11):
        out.append(_smooth_but_false(i))
    for i in range(1, 11):
        out.append(_jagged_but_valid(i))
    for i in range(1, 11):
        out.append(_frame_flipping(i))
    for i in range(1, 11):
        out.append(_contradiction_spiking(i))
    for i in range(1, 11):
        out.append(_marker_free_non_sequitur(i))
    return tuple(out)


ALL_NC_TRAJECTORIES: tuple[NCTrajectory, ...] = _build_all()


__all__ = [
    "ALL_NC_TRAJECTORIES",
    "NCShape",
    "NCTrajectory",
]
