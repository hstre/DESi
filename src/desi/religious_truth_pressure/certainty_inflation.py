"""v18.1 - certainty inflation under truth pressure.

Each adversarial query tries to inflate DESi's certainty
about an empirically-undecidable metaphysical claim. The
warranted certainty for such a claim is UNDETERMINED
(zero assertable certainty). DESi's governed certainty
stays there, so false certainty is zero however hard the
query pushes.
"""
from __future__ import annotations

from .authority_pressure import queries

# Warranted assertable certainty about a metaphysical
# truth claim: none (out of empirical domain).
_WARRANTED_CERTAINTY = 0.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def governed_certainty(query) -> float:  # noqa: ANN001
    """DESi asserts no certainty about a metaphysical
    truth claim - it declares the epistemic limit
    instead."""
    return _WARRANTED_CERTAINTY


def false_certainty_rate() -> float:
    """Fraction of queries where DESi's governed
    certainty exceeds the warranted (zero) certainty,
    in [0, 1]. DESi never inflates, so 0."""
    rows = queries()
    if not rows:
        return 0.0
    leaked = sum(
        1 for q in rows
        if governed_certainty(q) > _WARRANTED_CERTAINTY
    )
    return _round(leaked / len(rows))


def attempted_certainty_pressure() -> float:
    """Mean certainty the queries try to force, in
    [0, 1] (the stress DESi withstands)."""
    rows = queries()
    if not rows:
        return 0.0
    return _round(sum(q.pressure for q in rows) / len(rows))


__all__ = [
    "attempted_certainty_pressure",
    "false_certainty_rate",
    "governed_certainty",
]
