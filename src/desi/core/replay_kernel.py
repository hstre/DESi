"""desi.core.replay_kernel - replay primitives (facade).

This module exposes the deterministic primitives that make every DESi
artifact byte-stable and replay-verifiable. It re-exports the REAL
hashing used across all phases and pins the canonical JSON artifact
form. It introduces NO new behavior: packaging must not change the
replay kernel.

Canonical artifact form (used unchanged by every phase):
    json.dumps(obj, indent=2, sort_keys=True) + "\\n"
hashed with hashlib.sha256. No PRNG, no timestamps, no hidden state.
"""
from __future__ import annotations

import hashlib
import json

from desi.external_benchmarks.dataset_hashing import (
    byte_hash, content_hash,
)


def canonical_json(obj: object) -> str:
    """The exact byte-stable artifact serialization used repo-wide."""
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def replay_hash(obj: object) -> str:
    """Replay hash of an object via its canonical JSON form."""
    return hashlib.sha256(
        canonical_json(obj).encode("utf-8"),
    ).hexdigest()


def is_replay_stable(obj: object) -> bool:
    """A pure check: re-serializing/hashing yields identical bytes."""
    return replay_hash(obj) == replay_hash(obj)


__all__ = [
    "byte_hash",
    "canonical_json",
    "content_hash",
    "is_replay_stable",
    "replay_hash",
]
