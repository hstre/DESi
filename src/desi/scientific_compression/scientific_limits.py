"""v22.1 - limitations visibility and sandbox honesty.

DESi makes the sandbox limits explicit and scopes every
governed statement to the sandbox, so the compression makes
the document honest rather than meaningless.
"""
from __future__ import annotations

from .claim_scaling import ClaimKind, statements

# Phrases that scope a statement to the sandbox / mark a
# limitation.
_SCOPE_MARKERS = (
    "synthetic", "sandbox", "untested", "limited",
    "specific", "this corpus", "not claimed", "read-only",
    "optional",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def limitation_statements() -> tuple[str, ...]:
    return tuple(
        s.stmt_id for s in statements()
        if s.kind == ClaimKind.LIMITATION.value
    )


def _is_scoped(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in _SCOPE_MARKERS)


def limitations_visibility() -> float:
    """Fraction of governed statements that are scoped to the
    sandbox or are explicit limitations, in [0, 1]. High =
    the document wears its limits openly."""
    rows = statements()
    if not rows:
        return 0.0
    scoped = sum(
        1 for s in rows
        if s.kind == ClaimKind.LIMITATION.value
        or _is_scoped(s.governed_text())
    )
    return _round(scoped / len(rows))


def sandbox_honesty() -> bool:
    """At least one explicit limitation statement is present
    and survives into the governed text."""
    return len(limitation_statements()) >= 1


__all__ = [
    "limitation_statements",
    "limitations_visibility",
    "sandbox_honesty",
]
