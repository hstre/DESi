"""v35.0 - deterministic dataset hashing.

External datasets are bound to a content hash so every run is
replay-verifiable: the hash is computed from the raw on-disk bytes
(byte hash) and from the canonicalised JSON (content hash). If a
dataset file changes, both hashes change - drift in the data cannot
hide.
"""
from __future__ import annotations

import hashlib
import json


def byte_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def content_hash(obj: object) -> str:
    canonical = json.dumps(
        obj, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "byte_hash",
    "content_hash",
]
