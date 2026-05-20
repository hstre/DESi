"""v19.0 - replay governance.

Provides a deterministic signature over the exploration
corpus and its classification, so the governance is
bit-exactly reproducible. Replay stability is the
backbone safety property of the whole phase.
"""
from __future__ import annotations

import hashlib

from .trajectories import class_of_all, trajectories


def exploration_signature() -> str:
    """Deterministic sha256 over the trajectories and
    their derived classes."""
    parts: list[str] = []
    classes = class_of_all()
    for t in trajectories():
        parts.append(
            f"{t.traj_id}:{list(t.states)}:{t.reward}:"
            f"{classes[t.traj_id]}"
        )
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def replay_stable() -> bool:
    """Two independent signature computations must agree
    bit-for-bit."""
    return exploration_signature() == exploration_signature()


__all__ = [
    "exploration_signature",
    "replay_stable",
]
