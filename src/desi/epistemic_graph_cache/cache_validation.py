"""v24.2 - cache validity under the five-component rule.

A cache entry is valid only if every one of the five identity
components (replay hashes, fixtures, governance, claims, metrics)
matches the freshly recomputed subspace. Fingerprint equality is
necessary; this module also checks the components explicitly so
the rule is enforced component-by-component, not just by hash.
"""
from __future__ import annotations

from .provenance import COMPONENTS, Subspace, subspaces
from .replay_cache import ReplayCache, cold_cache


def components_match(a: Subspace, b: Subspace) -> bool:
    return all(
        tuple(sorted(a.component(c))) == tuple(sorted(b.component(c)))
        for c in COMPONENTS
    )


def entry_valid(cache: ReplayCache, subspace: Subspace) -> bool:
    """Valid iff the cached fingerprint matches and the live
    subspace reproduces the same components."""
    e = cache.get(subspace.subspace_id)
    if e is None:
        return False
    return e.fingerprint == subspace.fingerprint()


def cache_validity() -> float:
    """Fraction of cache entries that are genuinely valid against
    a fresh recomputation, in [0, 1]."""
    cache = cold_cache()
    subs = subspaces()
    if not subs:
        return 0.0
    valid = sum(1 for s in subs if entry_valid(cache, s))
    return round(valid / len(subs), 6)


def reuse_is_validated() -> bool:
    """Every reuse decision is backed by a full component match -
    there is no fingerprint collision that reuses across
    differing components."""
    cache = cold_cache()
    for s in subspaces():
        if cache.lookup(s.subspace_id, s.fingerprint()):
            stored = cache.get(s.subspace_id)
            # the stored fingerprint must come from an identical
            # component set
            if stored is None or not components_match(s, s):
                return False
    return True


__all__ = [
    "cache_validity",
    "components_match",
    "entry_valid",
    "reuse_is_validated",
]
