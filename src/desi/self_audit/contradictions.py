"""Contradiction detector — Aufgabe 5.

Two claim shapes count as a contradiction:

1. **Same key, different values** within the same document.
2. **Same referenced artifact + same key, different values** across
   the entire corpus.

Claims with empty ``key`` are excluded — they cannot meaningfully
contradict each other.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .claim import ExplicitClaim


@dataclass(frozen=True)
class Contradiction:
    key: str
    scope: str          # "document:<path>" or "artifact:<path>"
    values: tuple[str, ...]
    claim_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "scope": self.scope,
            "values": list(self.values),
            "claim_ids": list(self.claim_ids),
        }


def find_contradictions(
    claims: tuple[ExplicitClaim, ...],
) -> tuple[Contradiction, ...]:
    out: list[Contradiction] = []

    # Group within each document by key.
    by_doc_key: dict[tuple[str, str], list[ExplicitClaim]] = defaultdict(list)
    for c in claims:
        if not c.key:
            continue
        by_doc_key[(c.doc_path, c.key)].append(c)
    for (doc, key), group in by_doc_key.items():
        values = {c.value for c in group}
        if len(values) >= 2:
            out.append(Contradiction(
                key=key,
                scope=f"document:{doc}",
                values=tuple(sorted(values)),
                claim_ids=tuple(sorted(c.claim_id for c in group)),
            ))

    # Group across the corpus by (referenced_artifact, key).
    by_art_key: dict[tuple[str, str], list[ExplicitClaim]] = defaultdict(list)
    for c in claims:
        if not c.key or not c.referenced_artifact:
            continue
        by_art_key[(c.referenced_artifact, c.key)].append(c)
    for (art, key), group in by_art_key.items():
        values = {c.value for c in group}
        if len(values) >= 2:
            out.append(Contradiction(
                key=key,
                scope=f"artifact:{art}",
                values=tuple(sorted(values)),
                claim_ids=tuple(sorted(c.claim_id for c in group)),
            ))

    return tuple(sorted(out, key=lambda c: (c.scope, c.key)))


__all__ = ["Contradiction", "find_contradictions"]
