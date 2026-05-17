"""v3.95 — method-level temporal features for the
entangled (G_v316susp + E_v317h) pair.

Each anchor's "method signature" is the per-
dimension rise index - the first state at which
the dimension's value differs from its state-0
value. ``-1`` denotes "never rises across the
5-state trajectory".

The signatures cover:

* ``frame_id``           - frame transition timing
* ``branch_cost``        - branch history rise
* ``contradiction_load`` - contradiction timing
* ``support_state``      - support timing
* ``confidence``         - audit confidence rise
* plus the remaining 4 closed dimensions

A per-family majority signature is computed; the
``path_distance`` between two families is the
number of dimensions on which their majority
signatures differ.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
)
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..epistemic_trajectory.state import (
    DIMENSION_NAMES,
)
from ..novel_families import all_family_members


_NEVER_RISES: int = -1


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class MethodSignature:
    trajectory_id: str
    family_id: str
    rise_index: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "family_id": self.family_id,
            "rise_index_by_dim": {
                name: idx
                for name, idx in zip(
                    DIMENSION_NAMES,
                    self.rise_index,
                )
            },
        }


def _per_dim_rise(traj) -> tuple[int, ...]:
    out: list[int] = []
    for d_idx, name in enumerate(DIMENSION_NAMES):
        s0 = getattr(traj.states[0], name)
        rise = _NEVER_RISES
        for i, s in enumerate(traj.states):
            if getattr(s, name) != s0:
                rise = i
                break
        out.append(rise)
    return tuple(out)


@lru_cache(maxsize=1)
def _family_lookup() -> dict[str, str]:
    return {
        m: fid
        for fid, ms in all_family_members().items()
        for m in ms
    }


@lru_cache(maxsize=1)
def all_method_signatures() -> tuple[
    MethodSignature, ...,
]:
    members = set(entangled_members())
    fam = _family_lookup()
    out: list[MethodSignature] = []
    for t in extract_all_trajectories():
        if t.trajectory_id not in members:
            continue
        out.append(MethodSignature(
            trajectory_id=t.trajectory_id,
            family_id=fam.get(t.trajectory_id, "?"),
            rise_index=_per_dim_rise(t),
        ))
    return tuple(sorted(
        out, key=lambda s: s.trajectory_id,
    ))


def family_majority_signature(
    family_id: str,
) -> tuple[int, ...]:
    sigs = [
        s for s in all_method_signatures()
        if s.family_id == family_id
    ]
    if not sigs:
        return tuple([_NEVER_RISES] * len(DIMENSION_NAMES))
    out: list[int] = []
    for d_idx in range(len(DIMENSION_NAMES)):
        counts: dict[int, int] = {}
        for s in sigs:
            v = s.rise_index[d_idx]
            counts[v] = counts.get(v, 0) + 1
        # Most frequent, ties broken by smaller value.
        winner = sorted(
            counts.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )[0][0]
        out.append(winner)
    return tuple(out)


def path_distance() -> int:
    g_sig = family_majority_signature(
        ENTANGLED_FAMILY_IDS[0],
    )
    e_sig = family_majority_signature(
        ENTANGLED_FAMILY_IDS[1],
    )
    return sum(
        1 for a, b in zip(g_sig, e_sig) if a != b
    )


def method_overlap() -> float:
    """Fraction of state dimensions on which the
    two family majority signatures agree."""
    total = len(DIMENSION_NAMES)
    if total == 0:
        return 1.0
    return _round(1.0 - path_distance() / total)


def per_member_signature_distance_to_family(
    family_id: str,
) -> dict[str, int]:
    """For every anchor in the entangled pool,
    Hamming distance from the *foreign* family's
    majority signature - high values mean the
    anchor looks unlike the other family
    methodologically."""
    other = next(
        fid for fid in ENTANGLED_FAMILY_IDS
        if fid != family_id
    )
    other_sig = family_majority_signature(other)
    out: dict[str, int] = {}
    for s in all_method_signatures():
        if s.family_id != family_id:
            continue
        out[s.trajectory_id] = sum(
            1 for a, b in zip(s.rise_index, other_sig)
            if a != b
        )
    return out


__all__ = [
    "MethodSignature",
    "all_method_signatures",
    "family_majority_signature",
    "method_overlap",
    "path_distance",
    "per_member_signature_distance_to_family",
]
