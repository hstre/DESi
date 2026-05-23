"""v3.96 — feature-space construction for the
entangled (G_v316susp + E_v317h) resolution
attempt.

Combines three sources:

* ``RESIDUAL_DIMS``  - the v3.89 residual values
  for each of the 9 state dimensions (5 slots
  each = 45 values).
* ``TEMPORAL_DIMS``  - the v3.95 per-dim rise
  index (9 values per anchor).
* ``HIDDEN_DIMS``    - the v3.93 dominant_dims
  surface explicitly so the search can prioritise
  them.

A FeatureSpec selects a subset from these sources;
``feature_vector(spec)`` returns the projected
vector per anchor. ``-1`` rise values are remapped
to ``5`` so all temporal indices live in a non-
negative range.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..entangled.variance import (
    entangled_members,
    entangled_residual_vectors,
)
from ..entangled_method.method import (
    all_method_signatures,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9
_NEVER_RISES_REMAP: int = 5


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


RESIDUAL_DIMS: tuple[str, ...] = DIMENSION_NAMES
TEMPORAL_DIMS: tuple[str, ...] = tuple(
    f"temporal_{d}" for d in DIMENSION_NAMES
)


@dataclass(frozen=True)
class FeatureSpec:
    residual_dims: tuple[str, ...]
    temporal_dims: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "residual_dims":
                list(self.residual_dims),
            "temporal_dims":
                list(self.temporal_dims),
        }

    @property
    def size(self) -> int:
        return (
            len(self.residual_dims)
            + len(self.temporal_dims)
        )


def _residual_index(dim_name: str) -> tuple[int, ...]:
    d = DIMENSION_NAMES.index(dim_name)
    return tuple(
        s * _DIM_PER_STATE + d
        for s in range(_STATE_COUNT)
    )


def _temporal_offset_in_signature(
    temporal_dim_name: str,
) -> int:
    """temporal_<dim> ⇒ index of <dim> in
    DIMENSION_NAMES."""
    if not temporal_dim_name.startswith("temporal_"):
        raise ValueError(temporal_dim_name)
    base = temporal_dim_name.removeprefix(
        "temporal_",
    )
    return DIMENSION_NAMES.index(base)


@lru_cache(maxsize=1)
def _signature_map() -> dict[
    str, tuple[int, ...],
]:
    return {
        s.trajectory_id: s.rise_index
        for s in all_method_signatures()
    }


@lru_cache(maxsize=None)
def feature_vector(
    spec_residual: frozenset[str],
    spec_temporal: frozenset[str],
) -> dict[str, tuple[float, ...]]:
    res = entangled_residual_vectors()
    sigs = _signature_map()
    keep_res_idx: set[int] = set()
    for d in spec_residual:
        keep_res_idx.update(_residual_index(d))
    temporal_offsets = sorted(
        _temporal_offset_in_signature(d)
        for d in spec_temporal
    )
    out: dict[str, tuple[float, ...]] = {}
    for tid in entangled_members():
        if tid not in res:
            continue
        rvec = [
            res[tid][i] if i in keep_res_idx else 0.0
            for i in range(
                _STATE_COUNT * _DIM_PER_STATE,
            )
        ]
        sig = sigs.get(tid, ())
        tvec = []
        for off in temporal_offsets:
            v = sig[off] if off < len(sig) else _NEVER_RISES_REMAP
            tvec.append(
                float(
                    v if v >= 0
                    else _NEVER_RISES_REMAP,
                ),
            )
        out[tid] = tuple(rvec) + tuple(tvec)
    return out


def feature_vector_for_spec(
    spec: FeatureSpec,
) -> dict[str, tuple[float, ...]]:
    return feature_vector(
        frozenset(spec.residual_dims),
        frozenset(spec.temporal_dims),
    )


__all__ = [
    "FeatureSpec",
    "RESIDUAL_DIMS",
    "TEMPORAL_DIMS",
    "feature_vector",
    "feature_vector_for_spec",
]
