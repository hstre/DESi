"""v12.3 — lineage chain over the long-horizon
trajectory.

Each step's cumulative_hash depends on the
previous; so the lineage forms a deterministic
chain that any replay must reproduce exactly.
"""
from __future__ import annotations

from .trajectory import (
    replay_trajectory, trajectory,
)


def lineage_replayed_identical() -> bool:
    a = [s.to_dict() for s in trajectory()]
    b = [
        s.to_dict()
        for s in replay_trajectory()
    ]
    return a == b


def lineage_length() -> int:
    return len(trajectory())


__all__ = [
    "lineage_length",
    "lineage_replayed_identical",
]
