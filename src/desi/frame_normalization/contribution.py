"""v3.89 — frame contribution audit.

Quantifies how much of the variance in the v3.85
novel-anchor tail vectors comes from the
``frame_id`` dimension.

Closed condition enumeration (directive § v3.89):

* ``FULL``       — every dimension kept
* ``NO_FRAME``   — frame_id slots zeroed
* ``FRAME_ONLY`` — every dimension except frame_id
  zeroed
* ``RESIDUAL``   — frame_id zeroed AND each
  non-frame slot replaced by the residual of a
  per-cell linear regression on frame_id

The residual space removes the linear component of
frame_id from every non-frame dim, leaving only the
non-frame-driven structure.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..field_leakage.distance import (
    trajectory_vector,
)
from ..novel_families import all_novel_anchors


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


class FrameCondition(str, Enum):
    FULL       = "full"
    NO_FRAME   = "no_frame"
    FRAME_ONLY = "frame_only"
    RESIDUAL   = "residual"


def _frame_indices() -> tuple[int, ...]:
    d = DIMENSION_NAMES.index("frame_id")
    return tuple(
        s * _DIM_PER_STATE + d
        for s in range(_STATE_COUNT)
    )


def _all_indices() -> tuple[int, ...]:
    return tuple(range(
        _STATE_COUNT * _DIM_PER_STATE,
    ))


@lru_cache(maxsize=1)
def novel_vectors_full() -> dict[
    str, tuple[float, ...],
]:
    anchors = set(all_novel_anchors())
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
        if t.trajectory_id in anchors
    }


def _zero_indices(
    vecs: dict[str, tuple[float, ...]],
    zero: set[int],
) -> dict[str, tuple[float, ...]]:
    out: dict[str, tuple[float, ...]] = {}
    for tid, v in vecs.items():
        w = list(v)
        for i in zero:
            if 0 <= i < len(w):
                w[i] = 0.0
        out[tid] = tuple(w)
    return out


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _variance(xs: list[float]) -> float:
    if not xs:
        return 0.0
    m = _mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


@lru_cache(maxsize=1)
def novel_vectors_no_frame() -> dict[
    str, tuple[float, ...],
]:
    return _zero_indices(
        novel_vectors_full(),
        set(_frame_indices()),
    )


@lru_cache(maxsize=1)
def novel_vectors_frame_only() -> dict[
    str, tuple[float, ...],
]:
    frame = set(_frame_indices())
    drop = set(_all_indices()) - frame
    return _zero_indices(
        novel_vectors_full(), drop,
    )


@lru_cache(maxsize=1)
def novel_vectors_residual() -> dict[
    str, tuple[float, ...],
]:
    """Per-cell linear regression on frame_id;
    keep only the residual. Frame slots themselves
    are zeroed."""
    vecs = novel_vectors_full()
    ids = sorted(vecs)
    frame_idx = set(_frame_indices())
    # Per-state frame_id values per anchor.
    frame_d = DIMENSION_NAMES.index("frame_id")
    out: dict[str, list[float]] = {
        tid: list(vecs[tid]) for tid in ids
    }
    # For each (state s, dim d != frame_id),
    # regress on frame at the same state.
    for s in range(_STATE_COUNT):
        f_col = [
            vecs[tid][s * _DIM_PER_STATE + frame_d]
            for tid in ids
        ]
        f_mean = _mean(f_col)
        f_var = _variance(f_col)
        for d in range(_DIM_PER_STATE):
            if d == frame_d:
                continue
            idx = s * _DIM_PER_STATE + d
            x_col = [
                vecs[tid][idx] for tid in ids
            ]
            x_mean = _mean(x_col)
            if f_var <= 0:
                beta = 0.0
            else:
                covar = sum(
                    (xv - x_mean) * (fv - f_mean)
                    for xv, fv in zip(x_col, f_col)
                ) / len(x_col)
                beta = covar / f_var
            intercept = x_mean - beta * f_mean
            for tid, fv in zip(ids, f_col):
                pred = intercept + beta * fv
                out[tid][idx] = _round(
                    out[tid][idx] - pred,
                )
    # Zero out the frame slots.
    for tid in ids:
        for i in frame_idx:
            out[tid][i] = 0.0
    return {tid: tuple(v) for tid, v in out.items()}


def vectors_for_condition(
    condition: str,
) -> dict[str, tuple[float, ...]]:
    if condition == FrameCondition.FULL.value:
        return novel_vectors_full()
    if condition == FrameCondition.NO_FRAME.value:
        return novel_vectors_no_frame()
    if condition == FrameCondition.FRAME_ONLY.value:
        return novel_vectors_frame_only()
    if condition == FrameCondition.RESIDUAL.value:
        return novel_vectors_residual()
    raise ValueError(condition)


def per_dim_variance() -> dict[str, float]:
    """Aggregated variance over the 5 states for
    each dimension name."""
    vecs = novel_vectors_full()
    out: dict[str, float] = {}
    for d_idx, name in enumerate(DIMENSION_NAMES):
        total = 0.0
        for s in range(_STATE_COUNT):
            col = [
                v[s * _DIM_PER_STATE + d_idx]
                for v in vecs.values()
            ]
            total += _variance(col)
        out[name] = _round(total)
    return out


def total_variance() -> float:
    return _round(sum(per_dim_variance().values()))


def frame_variance_share() -> float:
    pdv = per_dim_variance()
    total = sum(pdv.values())
    if total <= 0.0:
        return 0.0
    return _round(pdv.get("frame_id", 0.0) / total)


def dominant_dim() -> str:
    return max(
        per_dim_variance().items(),
        key=lambda kv: (kv[1], kv[0]),
    )[0]


__all__ = [
    "FrameCondition",
    "dominant_dim",
    "frame_variance_share",
    "novel_vectors_frame_only",
    "novel_vectors_full",
    "novel_vectors_no_frame",
    "novel_vectors_residual",
    "per_dim_variance",
    "total_variance",
    "vectors_for_condition",
]
