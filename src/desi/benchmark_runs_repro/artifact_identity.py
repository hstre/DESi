"""v34.2 - identity checks across repeated runs.

Each identity metric is 1.0 iff the corresponding signature is the
same in every one of the repeated snapshots.
"""
from __future__ import annotations

from .repro_runner import snapshots


def _identical(key: str) -> bool:
    snaps = snapshots()
    if not snaps:
        return False
    first = snaps[0][key]
    return all(s[key] == first for s in snaps)


def output_identity() -> float:
    return 1.0 if _identical("output") else 0.0


def metric_identity() -> float:
    return 1.0 if _identical("metric") else 0.0


def citation_identity() -> float:
    return 1.0 if _identical("citation") else 0.0


def section_identity() -> float:
    return 1.0 if _identical("section") else 0.0


def artifact_identity() -> float:
    return 1.0 if _identical("artifact") else 0.0


def replay_hash_identity() -> float:
    return 1.0 if _identical("replay") else 0.0


__all__ = [
    "artifact_identity",
    "citation_identity",
    "metric_identity",
    "output_identity",
    "replay_hash_identity",
    "section_identity",
]
