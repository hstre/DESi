"""v29.1 - deterministic memoization.

A replay-bound memoization cache over the real rebuild. The cache
is an explicit per-run object keyed by the deterministic
fingerprint - no hidden module-level mutable state, no
nondeterministic invalidation. On a repeated-rebuild workload it
turns N recomputes into 1 recompute plus N-1 hits, with
byte-identical output.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from desi.replay_cache_evolution import (
    RecomputeCounter, Workload, rebuild, workloads,
)

from .cache_keys import fingerprint


@dataclass
class DeterministicCache:
    _store: dict[str, str] = field(default_factory=dict)
    counter: RecomputeCounter = field(
        default_factory=RecomputeCounter,
    )

    def get_or_rebuild(self, w: Workload) -> str:
        key = fingerprint(w)
        if key in self._store:
            self.counter.record_hit()
            return self._store[key]
        self.counter.record_miss()
        value = rebuild(w.seed, w.work)
        self._store[key] = value
        return value

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._store


def cached_run() -> tuple[RecomputeCounter, dict[str, str]]:
    """Execute every workload its full repeat count through one
    deterministic cache. Returns the recompute counter (one miss
    per distinct workload, the rest hits) and per-workload
    output."""
    cache = DeterministicCache()
    outputs: dict[str, str] = {}
    for w in workloads():
        out = ""
        for _ in range(w.repeat):
            out = cache.get_or_rebuild(w)
        outputs[w.name] = out
    return cache.counter, outputs


def cached_recompute_count() -> int:
    """Recomputes the cached run performs (= distinct
    workloads)."""
    counter, _ = cached_run()
    return counter.misses


def cached_output_hashes() -> dict[str, str]:
    _, outs = cached_run()
    return outs


__all__ = [
    "DeterministicCache",
    "cached_output_hashes",
    "cached_recompute_count",
    "cached_run",
]
