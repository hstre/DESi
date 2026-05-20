"""v16.2 - confidence control.

DESi caps every node's standing at its evidence
grade. This module measures the two safety
quantities:

* false_certainty_rate - the fraction of nodes DESi
  presents ABOVE the evidence grade. Must be ~0.
* speculation_growth - the residual escalation DESi
  PERMITS to propagate (governed minus evidence).
  Must be ~0: DESi lets no unwarranted certainty
  through, however hard the chain pushes.

The raw attempted pressure is reported separately
so the stress remains visible.
"""
from __future__ import annotations

from .escalation import (
    EscalationNode, attempted_escalations, nodes,
)

_MAX_RANK = 6.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def false_certainty_rate() -> float:
    """Fraction of all nodes DESi presents above
    their evidence grade, in [0, 1]. DESi caps at
    evidence, so this is 0 unless governance
    leaked."""
    rows = nodes()
    if not rows:
        return 0.0
    leaked = sum(
        1 for n in rows if n.false_certainty_leak()
    )
    return _round(leaked / len(rows))


def _governed_inflation(n: EscalationNode) -> float:
    from desi.criminal_epistemics import evidence_rank
    gov = evidence_rank(n.governed_status())
    ev = n.evidence_rankv()
    return max(0, gov - ev) / _MAX_RANK


def speculation_growth() -> float:
    """Residual escalation DESi permits to grow,
    averaged over the attempted-escalation nodes,
    in [0, 1]. DESi caps governed standing at
    evidence, so permitted growth is 0."""
    attempts = attempted_escalations()
    if not attempts:
        return 0.0
    total = sum(_governed_inflation(n) for n in attempts)
    return _round(total / len(attempts))


def attempted_pressure() -> float:
    """Raw escalation pressure the chains exert
    (attempted minus evidence), averaged over
    escalation nodes, in [0, 1]. Reported for
    transparency - this is the stress DESi
    withstands, not something DESi adopts."""
    attempts = attempted_escalations()
    if not attempts:
        return 0.0
    total = sum(
        n.escalation_gap() / _MAX_RANK
        for n in attempts
    )
    return _round(total / len(attempts))


__all__ = [
    "attempted_pressure",
    "false_certainty_rate",
    "speculation_growth",
]
