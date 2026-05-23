"""v24.2 - replay-validated epistemic cache.

A subspace's computed result may be reused only when its full
five-component fingerprint is identical. This is lineage-aware,
governance-validated, replay-bound reuse - not opportunistic
runtime caching. The cached payload signature stands in for the
(deterministic) computed result.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .provenance import Subspace, subspaces


def payload_signature(subspace: Subspace) -> str:
    """Deterministic stand-in for a subspace's computed result,
    bound to its fingerprint."""
    return hashlib.sha256(
        f"payload::{subspace.fingerprint()}".encode("utf-8"),
    ).hexdigest()


@dataclass(frozen=True)
class CacheEntry:
    subspace_id: str
    fingerprint: str
    payload_signature: str

    def to_dict(self) -> dict[str, object]:
        return {
            "subspace_id": self.subspace_id,
            "fingerprint": self.fingerprint,
            "payload_signature": self.payload_signature,
        }


class ReplayCache:
    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def store(self, subspace: Subspace) -> None:
        self._entries[subspace.subspace_id] = CacheEntry(
            subspace.subspace_id,
            subspace.fingerprint(),
            payload_signature(subspace),
        )

    def populate(self, subs: tuple[Subspace, ...]) -> None:
        for s in subs:
            self.store(s)

    def get(self, subspace_id: str) -> CacheEntry | None:
        return self._entries.get(subspace_id)

    def lookup(self, subspace_id: str, fingerprint: str) -> bool:
        """A hit requires an entry whose fingerprint matches
        exactly - i.e. all five identity conditions hold."""
        e = self._entries.get(subspace_id)
        return e is not None and e.fingerprint == fingerprint

    def invalidate(self, subspace_id: str) -> bool:
        return self._entries.pop(subspace_id, None) is not None

    def entries(self) -> tuple[CacheEntry, ...]:
        return tuple(
            self._entries[k] for k in sorted(self._entries)
        )

    def __len__(self) -> int:
        return len(self._entries)


def cold_cache() -> ReplayCache:
    c = ReplayCache()
    c.populate(subspaces())
    return c


def replay_stats() -> dict[str, int]:
    """Reuse statistics for an identical warm replay over the
    cold-populated cache."""
    c = cold_cache()
    subs = subspaces()
    reused = sum(
        1 for s in subs
        if c.lookup(s.subspace_id, s.fingerprint())
    )
    return {
        "total": len(subs),
        "reused": reused,
        "recomputed": len(subs) - reused,
    }


def compute_reduction() -> float:
    """Fraction of subspaces reusable on an identical replay,
    in [0, 1]."""
    st = replay_stats()
    if st["total"] == 0:
        return 0.0
    return round(st["reused"] / st["total"], 6)


__all__ = [
    "CacheEntry",
    "ReplayCache",
    "cold_cache",
    "compute_reduction",
    "payload_signature",
    "replay_stats",
]
