"""Historical drift detector — Aufgabe 6.

Walks the v2.x memory docs in order. For each ``key``, records the
sequence of asserted values as the version progresses. Any change
in value between two adjacent documents that reference the same
artifact path is a drift finding.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .claim import ExplicitClaim


@dataclass(frozen=True)
class DriftFinding:
    key: str
    artifact: str
    earlier_doc: str
    earlier_value: str
    later_doc: str
    later_value: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "artifact": self.artifact,
            "earlier_doc": self.earlier_doc,
            "earlier_value": self.earlier_value,
            "later_doc": self.later_doc,
            "later_value": self.later_value,
        }


_VERSION_PATTERN = re.compile(r"v(\d+)_(\d+)")


def _doc_version_key(doc_path: str) -> tuple[int, int, str]:
    """Sort docs by embedded version, then by path."""
    m = _VERSION_PATTERN.search(doc_path)
    if m:
        return (int(m.group(1)), int(m.group(2)), doc_path)
    return (99, 99, doc_path)


def find_drift(
    claims: tuple[ExplicitClaim, ...],
) -> tuple[DriftFinding, ...]:
    out: list[DriftFinding] = []
    # Bucket claims by (referenced_artifact, key); within each
    # bucket, sort by doc_version and emit a finding whenever the
    # value changes from one doc to the next.
    buckets: dict[
        tuple[str, str], list[ExplicitClaim]
    ] = defaultdict(list)
    for c in claims:
        if not c.referenced_artifact or not c.key:
            continue
        buckets[(c.referenced_artifact, c.key)].append(c)
    for (art, key), group in buckets.items():
        # Sort by version, then collapse duplicates per doc.
        per_doc: dict[str, str] = {}
        for c in sorted(group, key=lambda x: _doc_version_key(x.doc_path)):
            per_doc.setdefault(c.doc_path, c.value)
        sequence = sorted(per_doc.items(),
                          key=lambda kv: _doc_version_key(kv[0]))
        for (a_doc, a_val), (b_doc, b_val) in zip(
            sequence, sequence[1:],
        ):
            if a_val != b_val:
                out.append(DriftFinding(
                    key=key, artifact=art,
                    earlier_doc=a_doc, earlier_value=a_val,
                    later_doc=b_doc, later_value=b_val,
                ))
    return tuple(sorted(
        out, key=lambda d: (d.artifact, d.key, d.later_doc),
    ))


__all__ = ["DriftFinding", "find_drift"]
