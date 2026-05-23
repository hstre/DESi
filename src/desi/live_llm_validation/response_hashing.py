"""v38.0 - deterministic hashing of captured LLM responses.

The live LLM layer is the only stochastic part of DESi. Each raw
response is hashed so that, once captured, it is tamper-evident and
deterministically replayable: re-evaluation reads the captured bytes,
never the live API.
"""
from __future__ import annotations

import hashlib
import json


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_hash(record: dict) -> str:
    """Hash of the replay-relevant fields of a capture (raw content +
    model version + finish reason), independent of volatile metadata."""
    payload = {
        "raw_content": record.get("raw_content", ""),
        "model_version": record.get("model_version", ""),
        "finish_reason": record.get("finish_reason", ""),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__ = ["content_hash", "record_hash"]
