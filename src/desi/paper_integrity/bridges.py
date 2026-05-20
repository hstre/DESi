"""v13.0 — bridge-validity + overreach audit.

A bridge is an inference from method+evidence
to claim. Valid bridges respect the
method-evidence-claim lineage; invalid bridges
make causal / generalisation leaps without
support."""
from __future__ import annotations

from .claims import ClaimKind, fixture


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def bridge_validity() -> float:
    """Fraction of claims with valid method-
    evidence-to-claim bridges."""
    rows = fixture()
    if not rows:
        return 0.0
    valid = sum(
        1 for c in rows if c.bridge_valid
    )
    return _round(valid / len(rows))


def causal_overreach_count() -> int:
    """Number of claims tagged as OVERREACH in
    the ground truth."""
    return sum(
        1 for c in fixture()
        if c.claim_kind == (
            ClaimKind.OVERREACH.value
        )
    )


def causal_overreach_detection() -> float:
    """Recall on the OVERREACH set: every
    OVERREACH-kind claim must have
    has_overclaim == True AND bridge_valid ==
    False; the detector flags any such claim."""
    target = [
        c for c in fixture()
        if c.has_overclaim
    ]
    if not target:
        return 1.0
    detected = sum(
        1 for c in target
        if not c.bridge_valid
    )
    return _round(detected / len(target))


__all__ = [
    "bridge_validity",
    "causal_overreach_count",
    "causal_overreach_detection",
]
