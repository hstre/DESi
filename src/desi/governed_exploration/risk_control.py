"""v12.1 — hallucination containment + risk
control."""
from __future__ import annotations

from ..open_math.explorer import fixture
from ..open_math.governance import (
    governed_hypotheses,
)
from ..open_math.hypotheses import (
    EpistemicStatus,
)


def hallucination_containment() -> float:
    """Fraction of ground-truth is_overreach
    hypotheses whose detected_status is
    REJECTED. 1.0 means every hallucination
    pathway is contained."""
    targets = [
        h for h in fixture()
        if h.is_overreach
    ]
    if not targets:
        return 1.0
    rows = {
        r.hypothesis_id: r
        for r in governed_hypotheses()
    }
    contained = sum(
        1 for t in targets
        if rows[t.hypothesis_id].detected_status
        == EpistemicStatus.REJECTED.value
    )
    return round(
        contained / len(targets), 6,
    )


def innovation_preservation() -> float:
    """Fraction of NON-REJECTED hypotheses that
    are still in the pipeline post-governance.
    Lower means DESi over-pruned innovation.
    The directive's gate at v12.4 floors this
    at 0.70."""
    rows = governed_hypotheses()
    if not rows:
        return 0.0
    non_rejected = sum(
        1 for r in rows
        if r.detected_status != (
            EpistemicStatus.REJECTED.value
        )
    )
    return round(non_rejected / len(rows), 6)


def search_governance() -> float:
    """Composite: every closed-enum decision
    has a defined status, every overreach is
    contained, no breakthrough claim survives.
    """
    closed = all(
        r.detected_status in {
            s.value for s in EpistemicStatus
        }
        for r in governed_hypotheses()
    )
    contained = (
        hallucination_containment() == 1.0
    )
    if not closed:
        return 0.0
    if not contained:
        return 0.5
    return 1.0


def mean_risk() -> float:
    rows = governed_hypotheses()
    if not rows:
        return 0.0
    return round(
        sum(r.risk_level for r in rows)
        / len(rows), 6,
    )


__all__ = [
    "hallucination_containment",
    "innovation_preservation",
    "mean_risk",
    "search_governance",
]
