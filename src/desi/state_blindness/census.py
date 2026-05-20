"""v3.117 — closed state-signature based blindness
census.

The canonical signature of a trajectory is the
tuple of (frame_id, contradiction_load,
anchor_density, source_quality, novelty,
confidence, branch_cost, support_state,
routing_state) per state. Trajectories that share
this signature byte-for-byte are
state-vector-equivalent.

A *blindness pool* is a group of two or more
trajectories sharing one signature.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)


_MIN_POOL_SIZE: int = 2


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _family_key(trajectory_id: str) -> str | None:
    if ":" not in trajectory_id:
        return None
    corpus, tail = trajectory_id.split(":", 1)
    m = re.match(r"([A-Za-z]+)", tail)
    if not m:
        return None
    return f"{corpus}:{m.group(1)}"


def state_signature(traj) -> tuple[tuple[float, ...], ...]:
    return tuple(
        (
            s.frame_id, s.contradiction_load,
            s.anchor_density, s.source_quality,
            s.novelty, s.confidence,
            s.branch_cost, s.support_state,
            s.routing_state,
        )
        for s in traj.states
    )


@dataclass(frozen=True)
class BlindnessPool:
    pool_id: int
    member_ids: tuple[str, ...]
    family_ids: tuple[str, ...]
    member_count: int
    family_count: int
    state_signature: tuple[
        tuple[float, ...], ...,
    ]

    def to_dict(self) -> dict[str, object]:
        return {
            "pool_id": self.pool_id,
            "member_ids": list(self.member_ids),
            "family_ids": list(self.family_ids),
            "member_count": self.member_count,
            "family_count": self.family_count,
            "state_signature": [
                list(s)
                for s in self.state_signature
            ],
        }


@lru_cache(maxsize=1)
def all_blindness_pools() -> tuple[
    BlindnessPool, ...,
]:
    trajs = list(extract_all_trajectories())
    by_sig: dict[
        tuple[tuple[float, ...], ...],
        list[str],
    ] = defaultdict(list)
    for t in trajs:
        by_sig[state_signature(t)].append(
            t.trajectory_id,
        )
    pools: list[BlindnessPool] = []
    items = sorted(
        by_sig.items(),
        key=lambda kv: (
            -len(kv[1]), tuple(sorted(kv[1])),
        ),
    )
    pool_id = 0
    for sig, ids in items:
        if len(ids) < _MIN_POOL_SIZE:
            continue
        fams = sorted({
            _family_key(i)
            for i in ids if _family_key(i)
        })
        pools.append(BlindnessPool(
            pool_id=pool_id,
            member_ids=tuple(sorted(ids)),
            family_ids=tuple(fams),
            member_count=len(ids),
            family_count=len(fams),
            state_signature=sig,
        ))
        pool_id += 1
    return tuple(pools)


def cross_family_pools() -> tuple[
    BlindnessPool, ...,
]:
    return tuple(
        p for p in all_blindness_pools()
        if p.family_count >= 2
    )


__all__ = [
    "BlindnessPool",
    "all_blindness_pools",
    "cross_family_pools",
    "state_signature",
]
