"""desi.replay - stable facade for replay primitives and cache.

    from desi.replay import replay_kernel, DeterministicCache

Re-exports the replay kernel (canonical JSON + sha256 hashing) and the
real deterministic replay cache. No behavior is changed by packaging.
"""
from __future__ import annotations

from desi.core import replay_kernel
from desi.core.replay_kernel import (
    canonical_json, content_hash, is_replay_stable, replay_hash,
)
from desi.replay_cache_real import (
    DeterministicCache, replay_stability,
)

__all__ = [
    "DeterministicCache",
    "canonical_json",
    "content_hash",
    "is_replay_stable",
    "replay_hash",
    "replay_kernel",
    "replay_stability",
]
