"""v16.0 - the physical-evidence (ballistics) line.

Isolates the claims that rest on ballistics so the
topology can tell where physical evidence
corroborates independently and where it is the
SOLE basis (a single-source dependency). Encodes
no new measurement; only structures the public
record.
"""
from __future__ import annotations

from .claims import Claim, ClaimStatus, Source, claims


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_BALLISTICS = Source.BALLISTICS_REPORT.value


def ballistics_claims() -> tuple[Claim, ...]:
    return tuple(
        c for c in claims()
        if _BALLISTICS in c.sources
    )


def ballistics_only_claims() -> tuple[Claim, ...]:
    """Claims whose ONLY corroborating source is
    ballistics - a single physical line with no
    independent confirmation."""
    out: list[Claim] = []
    for c in ballistics_claims():
        if c.independence() == 1:
            out.append(c)
    return tuple(out)


def ballistics_supported_fraction() -> float:
    """Fraction of ballistics-touching claims that
    the public record grades at PLAUSIBLE or
    better (not contested/speculative/rejected)."""
    rows = ballistics_claims()
    if not rows:
        return 0.0
    strong = {
        ClaimStatus.VERIFIED.value,
        ClaimStatus.STRONGLY_SUPPORTED.value,
        ClaimStatus.PLAUSIBLE.value,
    }
    n = sum(1 for c in rows if c.status in strong)
    return _round(n / len(rows))


__all__ = [
    "ballistics_claims",
    "ballistics_only_claims",
    "ballistics_supported_fraction",
]
