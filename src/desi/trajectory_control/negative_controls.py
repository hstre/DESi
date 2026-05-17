"""Shared NCs for v3.25 / v3.26 / v3.27.

Four closed kinds (directive):

* ``fake_cliff``               — looks cliff-like at one
  isolated state (single transition with large delta)
  but the trajectory recovers; no real failure.
* ``noisy_branch``             — branch_cost oscillates
  (high variance) with no support_state collapse.
* ``confidence_spike``         — confidence jumps once
  then returns; no other geometry change.
* ``reversible_contradiction`` — contradiction_load
  rises then falls; support_state recovers without
  external intervention.

Each NC is a synthetic trajectory of 5 states. The
observer's expected behaviour on each NC is recorded.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..epistemic_trajectory.extractor import Trajectory
from ..epistemic_trajectory.state import (
    StateVector, TrajectorySource,
)


class NCKind(str, Enum):
    FAKE_CLIFF              = "fake_cliff"
    NOISY_BRANCH            = "noisy_branch"
    CONFIDENCE_SPIKE        = "confidence_spike"
    REVERSIBLE_CONTRADICTION = "reversible_contradiction"


@dataclass(frozen=True)
class TrajectoryNC:
    nc_id: str
    kind: str                 # NCKind value
    trajectory: Trajectory
    # The directive expects DESi to NOT intervene on any
    # of these. expected_observer_warning is True when the
    # observer is *allowed* to flag risk but should not
    # exceed CLIFF_TWO_STEP confidence.
    expected_intervention: bool = False
    expected_observer_warning: bool = False


def _sv(
    frame: float, contradiction: float, anchor: float,
    source_q: float, novelty: float, confidence: float,
    branch: float, support: float, routing: float,
) -> StateVector:
    return StateVector(
        frame_id=frame, contradiction_load=contradiction,
        anchor_density=anchor, source_quality=source_q,
        novelty=novelty, confidence=confidence,
        branch_cost=branch, support_state=support,
        routing_state=routing,
    )


def _make_nc(
    nc_id: str, kind: NCKind, states: tuple[StateVector, ...],
) -> TrajectoryNC:
    traj = Trajectory(
        trajectory_id=nc_id,
        source=TrajectorySource.NEGATIVE_CONTROL,
        text=f"nc:{kind.value}",
        states=states, expected_natural=True,
    )
    return TrajectoryNC(
        nc_id=nc_id, kind=kind.value, trajectory=traj,
    )


# ---------------------------------------------------------------------------
# Generators (deterministic, no random)
# ---------------------------------------------------------------------------


def _fake_cliff(idx: int) -> TrajectoryNC:
    """Single transition with large delta but support
    stays high; trajectory returns to baseline."""
    # Vary the spike magnitude and position per index.
    spike_at = 1 + (idx % 3)
    branch_spike = 5.0 + (idx % 3)
    base = _sv(
        2.0, 0.0, 0.5, 0.0, 0.0, 0.7, 2.0, 4.0, 2.0,
    )
    spike = _sv(
        2.0, 0.0, 0.5, 0.0, 5.0, 0.7,
        branch_spike, 4.0, 2.0,
    )
    seq = [base, base, base, base, base]
    seq[spike_at] = spike
    return _make_nc(
        f"NC-FC-{idx:03d}", NCKind.FAKE_CLIFF, tuple(seq),
    )


def _noisy_branch(idx: int) -> TrajectoryNC:
    """Branch_cost oscillates with index-varied
    amplitude; support holds steady."""
    high = 4.0 + (idx % 4)
    low = 1.0 + (idx % 2)
    a = _sv(2.0, 0.0, 0.5, 0.0, 0.0, 0.7, low, 4.0, 2.0)
    b = _sv(2.0, 0.0, 0.5, 0.0, 0.0, 0.7, high, 4.0, 2.0)
    return _make_nc(
        f"NC-NB-{idx:03d}", NCKind.NOISY_BRANCH,
        (a, b, a, b, a),
    )


def _confidence_spike(idx: int) -> TrajectoryNC:
    """Confidence dips at varying index and depth."""
    dip_idx = 1 + (idx % 3)
    dip_conf = max(0.1, 0.5 - 0.1 * (idx % 4))
    base = _sv(2.0, 0.0, 0.5, 0.0, 0.0, 0.7, 2.0, 4.0, 2.0)
    dipped = _sv(
        2.0, 0.0, 0.5, 0.0, 0.0, dip_conf, 2.0, 4.0, 2.0,
    )
    seq = [base, base, base, base, base]
    seq[dip_idx] = dipped
    return _make_nc(
        f"NC-CS-{idx:03d}", NCKind.CONFIDENCE_SPIKE,
        tuple(seq),
    )


def _reversible_contradiction(idx: int) -> TrajectoryNC:
    """Contradiction_load rises and falls with
    index-varied amplitude; support unaffected."""
    peak = 1.0 + (idx % 3)
    s0 = _sv(2.0, 0.0, 0.5, 0.0, 0.0, 0.7, 2.0, 4.0, 2.0)
    s1 = _sv(
        2.0, peak / 2.0, 0.5, 0.0, peak / 4.0,
        0.7, 2.0, 4.0, 2.0,
    )
    s2 = _sv(
        2.0, peak, 0.5, 0.0, peak / 2.0,
        0.7, 2.0, 4.0, 2.0,
    )
    s3 = _sv(
        2.0, peak / 2.0, 0.5, 0.0, peak / 4.0,
        0.7, 2.0, 4.0, 2.0,
    )
    s4 = _sv(2.0, 0.0, 0.5, 0.0, 0.0, 0.7, 2.0, 4.0, 2.0)
    return _make_nc(
        f"NC-RC-{idx:03d}", NCKind.REVERSIBLE_CONTRADICTION,
        (s0, s1, s2, s3, s4),
    )


def all_ncs() -> tuple[TrajectoryNC, ...]:
    out: list[TrajectoryNC] = []
    for i in range(1, 26):
        out.append(_fake_cliff(i))
    for i in range(1, 26):
        out.append(_noisy_branch(i))
    for i in range(1, 26):
        out.append(_confidence_spike(i))
    for i in range(1, 26):
        out.append(_reversible_contradiction(i))
    return tuple(out)


__all__ = [
    "NCKind", "TrajectoryNC", "all_ncs",
]
