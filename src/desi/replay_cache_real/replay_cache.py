"""v29.1 - lineage-aware cache invalidation.

A cached entry may be reused only when its stored fingerprint
matches the current one. Any change in a lineage component yields
a different fingerprint, so the stale entry is rejected (a miss)
and the correct value is recomputed. This is the replay-bound
invalidation rule - no nondeterministic invalidation, no reuse
across differing inputs.
"""
from __future__ import annotations

from desi.replay_cache_evolution import workloads

from .cache_keys import (
    _COMPONENTS, fingerprint, perturbed_fingerprint,
)
from .memoization import DeterministicCache


def is_stale(stored_fp: str, current_fp: str) -> bool:
    return stored_fp != current_fp


def stale_rejected_for(w) -> bool:
    """A populated cache must reject every perturbed (stale)
    fingerprint of a workload across all lineage components."""
    cache = DeterministicCache()
    cache.get_or_rebuild(w)  # populate with the valid key
    valid = fingerprint(w)
    for comp in _COMPONENTS:
        stale = perturbed_fingerprint(w, comp)
        if not is_stale(valid, stale):
            return False
        if stale in cache:  # stale key must not hit
            return False
    return True


def stale_state_rejection() -> float:
    """Fraction of workloads for which every stale fingerprint is
    rejected, in [0, 1]."""
    ws = workloads()
    if not ws:
        return 0.0
    ok = sum(1 for w in ws if stale_rejected_for(w))
    return round(ok / len(ws), 6)


def valid_reuse_for(w) -> bool:
    """A valid (unchanged) fingerprint is reused (a hit)."""
    cache = DeterministicCache()
    cache.get_or_rebuild(w)
    return fingerprint(w) in cache


__all__ = [
    "is_stale",
    "stale_rejected_for",
    "stale_state_rejection",
    "valid_reuse_for",
]
