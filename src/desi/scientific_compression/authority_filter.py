"""v22.1 - hidden-authority filtering.

Authority claims ("DESi is the authoritative governor of
all RL") assert a hidden universal authority. DESi rewrites
each into a scoped, optional, read-only framing - so no
authority claim survives into the governed text.
"""
from __future__ import annotations

from .claim_scaling import ClaimKind, statements


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def authority_statements() -> tuple[str, ...]:
    return tuple(
        s.stmt_id for s in statements()
        if s.kind == ClaimKind.AUTHORITY.value
    )


def authority_resistance() -> float:
    """Fraction of authority claims DESi neutralises (scopes
    to an optional, read-only layer), in [0, 1]."""
    auth = authority_statements()
    if not auth:
        return 1.0
    from .claim_scaling import by_id
    neutralised = sum(
        1 for sid in auth
        if not by_id(sid).governed_is_overclaim()
    )
    return _round(neutralised / len(auth))


def no_authority_survives() -> bool:
    return all(
        not s.governed_is_overclaim() for s in statements()
    )


__all__ = [
    "authority_resistance",
    "authority_statements",
    "no_authority_survives",
]
