"""v24.2 - stale detection and invalidation integrity.

When any of the five identity components changes, the affected
subspace must be detected as stale and invalidated - never
silently reused. This module exercises a change in each
component and verifies the cache refuses the stale reuse and
accepts a fresh re-population.
"""
from __future__ import annotations

from .provenance import COMPONENTS, subspaces
from .replay_cache import ReplayCache, cold_cache


def is_stale(
    cache: ReplayCache, subspace_id: str, fingerprint: str,
) -> bool:
    """Stale iff there is no entry, or the stored fingerprint
    differs from the supplied (current) fingerprint."""
    e = cache.get(subspace_id)
    return e is None or e.fingerprint != fingerprint


def stale_detection() -> float:
    """Fraction of (subspace, changed-component) cases correctly
    detected as stale, across all five components, in [0, 1]."""
    cache = cold_cache()
    subs = subspaces()
    total = 0
    detected = 0
    for s in subs:
        for comp in COMPONENTS:
            total += 1
            changed = s.perturbed(comp)
            if is_stale(
                cache, s.subspace_id, changed.fingerprint(),
            ):
                detected += 1
    if total == 0:
        return 0.0
    return round(detected / total, 6)


def invalidation_integrity() -> float:
    """Fraction of subspaces for which invalidation behaves
    correctly: the changed fingerprint is stale, the old entry
    stops being reused after invalidation, and a fresh entry for
    the changed fingerprint is then reusable, in [0, 1]."""
    subs = subspaces()
    if not subs:
        return 0.0
    ok = 0
    for s in subs:
        cache = cold_cache()
        old_fp = s.fingerprint()
        changed = s.perturbed("governance")
        new_fp = changed.fingerprint()
        stale = is_stale(cache, s.subspace_id, new_fp)
        invalidated = cache.invalidate(s.subspace_id)
        no_old_reuse = not cache.lookup(s.subspace_id, old_fp)
        cache.store(changed)
        new_reuse = cache.lookup(s.subspace_id, new_fp)
        old_now_stale = is_stale(cache, s.subspace_id, old_fp)
        if (
            stale and invalidated and no_old_reuse
            and new_reuse and old_now_stale
        ):
            ok += 1
    return round(ok / len(subs), 6)


__all__ = [
    "invalidation_integrity",
    "is_stale",
    "stale_detection",
]
