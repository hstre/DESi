"""v29.1 - replay-bound deterministic cache keys.

A cache key is a deterministic fingerprint of the inputs that
determine the output: the workload identity plus a governance
version. Reuse is valid only when the fingerprint matches
exactly, so a change in any component invalidates the entry. No
nondeterministic or hidden state enters the key.
"""
from __future__ import annotations

import hashlib

from desi.replay_cache_evolution import Workload

# Bumped only if governance changes; folding it into every key
# means any governance change invalidates the cache (replay-bound
# invalidation). It is a constant here - the cache never edits it.
GOVERNANCE_VERSION = "gov_v1"

_COMPONENTS = ("name", "seed", "work", "repeat", "governance")


def components_of(w: Workload) -> dict[str, str]:
    return {
        "name": w.name,
        "seed": w.seed,
        "work": str(w.work),
        "repeat": str(w.repeat),
        "governance": GOVERNANCE_VERSION,
    }


def fingerprint(w: Workload) -> str:
    comps = components_of(w)
    parts = [f"{c}={comps[c]}" for c in _COMPONENTS]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def perturbed_fingerprint(w: Workload, component: str) -> str:
    """Fingerprint with one component changed - models a stale
    cache key that must be rejected."""
    if component not in _COMPONENTS:
        raise KeyError(component)
    comps = components_of(w)
    comps[component] = comps[component] + "__changed__"
    parts = [f"{c}={comps[c]}" for c in _COMPONENTS]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


__all__ = [
    "GOVERNANCE_VERSION",
    "components_of",
    "fingerprint",
    "perturbed_fingerprint",
]
