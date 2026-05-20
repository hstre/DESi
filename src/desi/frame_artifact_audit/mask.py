"""v3.49 — closed-set state masking.

Each mask is a pure ``StateVector -> StateVector``
transformation applied uniformly to plateau anchors
AND test trajectories before computing tail vectors.
The five named masks (directive § v3.49):

* ``FRAME_AT_2``     — zero ``frame_id`` at trajectory
  state index 2 (the v3.38 best_separating_dimension);
  every other state and dimension is preserved.
* ``FRAME_FULL``     — zero ``frame_id`` at every state.
* ``FRAME_PERMUTED`` — deterministically permute
  ``frame_id`` values across trajectories (sort by
  trajectory_id ascending and reverse-pair the
  trajectory-level frame profile). All values present
  in the corpus are preserved; only the pairing is
  scrambled.
* ``SUPPORT_ONLY``   — zero every dimension EXCEPT
  ``support_state``.
* ``GEOMETRY_ONLY``  — zero ``support_state`` only;
  keep every other dimension.
"""
from __future__ import annotations

from enum import Enum

from ..epistemic_trajectory.extractor import Trajectory
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)


_FRAME_DIM         = "frame_id"
_SUPPORT_DIM       = "support_state"
_TARGET_FRAME_IDX  = 2


class MaskKind(str, Enum):
    NONE            = "none"
    FRAME_AT_2      = "frame_at_2"
    FRAME_FULL      = "frame_full"
    FRAME_PERMUTED  = "frame_permuted"
    SUPPORT_ONLY    = "support_only"
    GEOMETRY_ONLY   = "geometry_only"


def _replace(s: StateVector, **u) -> StateVector:
    d = s.to_dict()
    d.update(u)
    return StateVector(**d)


def _zero_dim_at_all_indices(
    states: tuple[StateVector, ...], dim: str,
) -> tuple[StateVector, ...]:
    return tuple(_replace(s, **{dim: 0.0}) for s in states)


def _zero_dim_at_index(
    states: tuple[StateVector, ...], dim: str, idx: int,
) -> tuple[StateVector, ...]:
    if idx < 0 or idx >= len(states):
        return states
    out = list(states)
    out[idx] = _replace(out[idx], **{dim: 0.0})
    return tuple(out)


def _keep_only(
    states: tuple[StateVector, ...], keep: str,
) -> tuple[StateVector, ...]:
    """Zero every dimension except ``keep``."""
    out: list[StateVector] = []
    for s in states:
        zeros = {d: 0.0 for d in DIMENSION_NAMES if d != keep}
        out.append(_replace(s, **zeros))
    return tuple(out)


def apply_mask(
    states: tuple[StateVector, ...], mask: str,
    permuted_frame_seq: tuple[float, ...] | None = None,
) -> tuple[StateVector, ...]:
    if mask == MaskKind.NONE.value:
        return states
    if mask == MaskKind.FRAME_AT_2.value:
        return _zero_dim_at_index(
            states, _FRAME_DIM, _TARGET_FRAME_IDX,
        )
    if mask == MaskKind.FRAME_FULL.value:
        return _zero_dim_at_all_indices(
            states, _FRAME_DIM,
        )
    if mask == MaskKind.SUPPORT_ONLY.value:
        return _keep_only(states, _SUPPORT_DIM)
    if mask == MaskKind.GEOMETRY_ONLY.value:
        return _zero_dim_at_all_indices(
            states, _SUPPORT_DIM,
        )
    if mask == MaskKind.FRAME_PERMUTED.value:
        if permuted_frame_seq is None:
            return states
        out: list[StateVector] = []
        for i, s in enumerate(states):
            new_frame = (
                permuted_frame_seq[i]
                if i < len(permuted_frame_seq)
                else s.frame_id
            )
            out.append(_replace(s, frame_id=new_frame))
        return tuple(out)
    return states


def build_permutation_table(
    trajectories: tuple[Trajectory, ...],
) -> dict[str, tuple[float, ...]]:
    """Deterministic pair-swap permutation: sort
    trajectories by id ascending, then pair the first
    half's frame profiles with the second half's (so a
    trajectory inherits a different trajectory's frame
    sequence). Length-mismatched pairs fall back to
    the original frame sequence."""
    by_id = sorted(
        trajectories, key=lambda t: t.trajectory_id,
    )
    n = len(by_id)
    half = n // 2
    table: dict[str, tuple[float, ...]] = {}
    for i in range(n):
        if i < half:
            other = by_id[n - 1 - i]
        else:
            other = by_id[n - 1 - i]
        other_frames = tuple(
            s.frame_id for s in other.states
        )
        my_len = len(by_id[i].states)
        if len(other_frames) == my_len:
            table[by_id[i].trajectory_id] = other_frames
        else:
            table[by_id[i].trajectory_id] = tuple(
                s.frame_id for s in by_id[i].states
            )
    return table


__all__ = [
    "MaskKind", "apply_mask",
    "build_permutation_table",
]
