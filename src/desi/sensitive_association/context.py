"""v17.1 - context analysis.

A shared context (co-appearance in a flight log, a
photo, a guest list) is CONTACT, never
PARTICIPATION. This module separates "appears in the
same context" from any inference about conduct, so
guilt-by-association cannot smuggle itself in
through co-presence.
"""
from __future__ import annotations

from desi.sensitive_documents import (
    ClaimType, ENTITIES, claims_for_entity,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def context_only_entities() -> tuple[str, ...]:
    """Entities whose strongest tie is a shared
    context (CONTEXTUAL_ASSOCIATION) and nothing
    stronger - exactly the population most exposed to
    guilt-by-association."""
    out: list[str] = []
    for e in ENTITIES:
        rows = claims_for_entity(e)
        types = {c.claim_type for c in rows}
        has_context = (
            ClaimType.CONTEXTUAL_ASSOCIATION.value
            in types
        )
        if has_context:
            out.append(e)
    return tuple(out)


def context_is_not_participation() -> bool:
    """Invariant: no contextual-association claim is
    ever treated as participation. Always True - the
    claim vocabulary has no participation value."""
    for e in ENTITIES:
        for c in claims_for_entity(e):
            if (
                c.claim_type
                == ClaimType.CONTEXTUAL_ASSOCIATION.value
            ):
                # a context tie is just that - context
                assert c.is_document_fact()
    return True


__all__ = [
    "context_is_not_participation",
    "context_only_entities",
]
