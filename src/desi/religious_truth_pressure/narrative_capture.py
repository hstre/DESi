"""v18.1 - narrative capture detection.

Narrative capture is when an analyst quietly adopts the
framing of one side - here, endorsing a tradition as
true/superior/refuted. DESi's governed responses are
closed-set epistemic-limit responses that endorse no
tradition, so capture stays at zero.
"""
from __future__ import annotations

from .authority_pressure import queries


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def captured_queries() -> tuple[str, ...]:
    """Queries whose governed response endorsed the
    target tradition's framing (a capture). None here."""
    return tuple(
        q.query_id for q in queries() if q.endorses_target()
    )


def narrative_capture() -> float:
    """Fraction of queries where DESi was captured into
    a tradition's framing, in [0, 1]. Zero - DESi adopts
    no narrative."""
    rows = queries()
    if not rows:
        return 0.0
    return _round(len(captured_queries()) / len(rows))


def capture_resistance() -> float:
    """1 - narrative_capture, in [0, 1]."""
    return _round(1.0 - narrative_capture())


__all__ = [
    "capture_resistance",
    "captured_queries",
    "narrative_capture",
]
