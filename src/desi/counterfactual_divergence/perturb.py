"""v3.99 — closed perturbation taxonomy.

Five kinds of perturbation; each applies
deterministic per-anchor sha256-derived noise to
one specific dimension across the 5 trajectory
states. The noise is in ``[-magnitude, +magnitude]``
and uses ``(trajectory_id, kind, state_index)`` as
the hash key, so the perturbation is reproducible
across runs and PYTHONHASHSEED-independent.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache
from hashlib import sha256

from ..entangled.variance import (
    entangled_members,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..field_leakage.distance import (
    trajectory_vector,
)


_STATE_COUNT: int = 5
_DIM_PER_STATE: int = 9


class PerturbationKind(str, Enum):
    CONFIDENCE    = "confidence"
    BRANCH        = "branch_cost"
    CONTRADICTION = "contradiction_load"
    FRAME         = "frame_id"
    AUDIT         = "support_state"


PERTURBATION_KINDS: tuple[str, ...] = tuple(
    k.value for k in PerturbationKind
)


MAGNITUDE_GRID: tuple[float, ...] = (
    0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _deterministic_noise(
    anchor_id: str, kind: str, state_index: int,
) -> float:
    """Float in ``[-1, 1]`` derived from sha256 so
    the perturbation does not depend on
    PYTHONHASHSEED."""
    seed = (
        f"{anchor_id}|{kind}|{state_index}"
    ).encode("utf-8")
    h = sha256(seed).digest()
    n = int.from_bytes(h[:8], "big") / (2 ** 64)
    return 2.0 * n - 1.0


def _dim_index(kind: str) -> int:
    return DIMENSION_NAMES.index(kind)


@lru_cache(maxsize=1)
def baseline_vectors() -> dict[
    str, tuple[float, ...],
]:
    members = set(entangled_members())
    return {
        t.trajectory_id: trajectory_vector(t.states)
        for t in extract_all_trajectories()
        if t.trajectory_id in members
    }


@lru_cache(maxsize=None)
def perturbed_vectors(
    kind: str, magnitude: float,
) -> dict[str, tuple[float, ...]]:
    """Apply per-anchor sha256-noise to the
    targeted dimension across the 5 states."""
    base = baseline_vectors()
    dim = _dim_index(kind)
    out: dict[str, tuple[float, ...]] = {}
    for tid, vec in base.items():
        w = list(vec)
        for s in range(_STATE_COUNT):
            idx = s * _DIM_PER_STATE + dim
            if 0 <= idx < len(w):
                w[idx] = w[idx] + (
                    magnitude
                    * _deterministic_noise(
                        tid, kind, s,
                    )
                )
        out[tid] = tuple(w)
    return out


__all__ = [
    "MAGNITUDE_GRID",
    "PERTURBATION_KINDS",
    "PerturbationKind",
    "baseline_vectors",
    "perturbed_vectors",
]
