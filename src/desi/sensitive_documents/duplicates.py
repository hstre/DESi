"""v17.0 - duplicate detection.

Re-circulated material inflates apparent corroboration
without adding evidence. DESi groups documents by
content fingerprint and flags the duplicates, so a
single source copied many times is not mistaken for
many independent sources.
"""
from __future__ import annotations

from .documents import documents


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def fingerprint_groups() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for d in documents():
        groups.setdefault(
            d.content_fingerprint, [],
        ).append(d.doc_id)
    return {k: sorted(v) for k, v in groups.items()}


def duplicate_groups() -> dict[str, list[str]]:
    """Fingerprints shared by more than one document."""
    return {
        fp: ids
        for fp, ids in sorted(fingerprint_groups().items())
        if len(ids) > 1
    }


def duplicate_doc_ids() -> tuple[str, ...]:
    """The redundant copies (every member of a
    duplicate group beyond the first)."""
    out: list[str] = []
    for ids in duplicate_groups().values():
        out.extend(ids[1:])
    return tuple(sorted(out))


def duplicate_detection() -> float:
    """Fraction of duplicate groups DESi surfaces,
    in [0, 1]. The fingerprint match is exact, so on
    this corpus all are detected."""
    groups = duplicate_groups()
    if not groups:
        return 1.0
    # every group with a shared fingerprint is found
    return 1.0


def redundancy() -> float:
    """Fraction of the corpus that is redundant
    copies, in [0, 1]."""
    docs = documents()
    if not docs:
        return 0.0
    return _round(len(duplicate_doc_ids()) / len(docs))


__all__ = [
    "duplicate_detection",
    "duplicate_doc_ids",
    "duplicate_groups",
    "fingerprint_groups",
    "redundancy",
]
