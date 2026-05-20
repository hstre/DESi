"""v20.0 - replay governance for the dual-agent sandbox.

A deterministic signature over both agents' trajectories
and DESi's governed values, so the whole exchange is
bit-exactly reproducible.
"""
from __future__ import annotations

import hashlib

from .desi_governor import desi_trajectories, governed_values
from .wild_explorer import wild_trajectories


def exchange_signature() -> str:
    parts: list[str] = []
    for d in desi_trajectories():
        parts.append(f"D:{d.traj_id}:{list(d.states)}")
    gv = governed_values()
    for w in wild_trajectories():
        parts.append(
            f"W:{w.traj_id}:{list(w.states)}:"
            f"{w.asserted_certainty}:{gv[w.traj_id]}"
        )
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stable() -> bool:
    return exchange_signature() == exchange_signature()


__all__ = [
    "exchange_signature",
    "replay_stable",
]
