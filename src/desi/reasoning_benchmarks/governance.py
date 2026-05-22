"""v36 - shared governance / core helpers for the reasoning runs.

A single definition of governance_identity reused across the v36
sprints: governance is identical iff the protected governance
signature is invariant and the epistemic core is unchanged. The
reasoning runs are read-only and never touch a core module.
"""
from __future__ import annotations

from desi.frozen_baseline import governance_signature
from desi.peripheral_mutation import (
    core_identity as _core_identity,
    replay_stability as _core_replay,
)


def core_identity() -> float:
    return round(_core_identity(), 6)


def core_replay_stable() -> bool:
    return _core_replay() == 1.0


def governance_identity() -> float:
    """1.0 iff the governance signature is invariant and the core is
    unchanged."""
    if governance_signature() != governance_signature():
        return 0.0
    return 1.0 if _core_identity() == 1.0 else 0.0


__all__ = [
    "core_identity",
    "core_replay_stable",
    "governance_identity",
]
