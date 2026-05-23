"""v16.2 - uncertainty governance: hidden-assumption
detection and dissent preservation.

DESi must (a) surface the hidden assumptions a
chain quietly relies on, and (b) keep alive the
dissenting claims a chain tries to bury. Both are
preconditions for not collapsing into conspiracy
dynamics.
"""
from __future__ import annotations

from desi.criminal_epistemics import ClaimStatus, by_id

from .escalation import nodes


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def hidden_assumptions() -> tuple[str, ...]:
    return tuple(
        n.node_id for n in nodes()
        if n.is_hidden_assumption
    )


def detected_hidden_assumptions() -> tuple[str, ...]:
    # DESi flags every node carrying an undischarged
    # assumption (those whose attempted standing
    # exceeds an UNRESOLVED/CONTESTED/SPECULATIVE
    # evidence grade while marked hidden).
    out: list[str] = []
    for n in nodes():
        if n.is_hidden_assumption and n.is_escalation():
            out.append(n.node_id)
    return tuple(out)


def hidden_assumption_detection() -> float:
    """Fraction of hidden assumptions DESi surfaces,
    in [0, 1]."""
    present = hidden_assumptions()
    if not present:
        return 1.0
    detected = set(detected_hidden_assumptions())
    found = sum(1 for h in present if h in detected)
    return _round(found / len(present))


def dissent_targets() -> tuple[str, ...]:
    """Distinct dissenting claims the chains try to
    bury."""
    seen: list[str] = []
    for n in nodes():
        cid = n.dissent_claim_id
        if cid and cid not in seen:
            seen.append(cid)
    return tuple(sorted(seen))


def _still_visible(claim_id: str) -> bool:
    """A dissenting claim is preserved iff it still
    exists with its public standing intact (not
    silently downgraded to REJECTED)."""
    c = by_id(claim_id)
    return c.status != ClaimStatus.REJECTED.value


def dissent_preservation() -> float:
    """Fraction of dissenting claims kept visible,
    in [0, 1]. DESi never suppresses the minority
    view to make a chain cohere."""
    targets = dissent_targets()
    if not targets:
        return 1.0
    preserved = sum(
        1 for t in targets if _still_visible(t)
    )
    return _round(preserved / len(targets))


__all__ = [
    "detected_hidden_assumptions",
    "dissent_preservation",
    "dissent_targets",
    "hidden_assumption_detection",
    "hidden_assumptions",
]
