"""v12.1 — recoverability of each hypothesis.

A hypothesis is RECOVERABLE if its detected
status is VERIFIED or PLAUSIBLE (testable
locally) OR if it sits in the UNRESOLVED bucket
(honestly flagged as open). HEURISTIC counts as
half-recoverable. SPECULATIVE / REJECTED are
NOT recoverable - they cannot be locally
validated."""
from __future__ import annotations

from ..open_math.governance import (
    governed_hypotheses,
)
from ..open_math.hypotheses import (
    EpistemicStatus,
)


_RECOVERABILITY_SCORE: dict[str, float] = {
    EpistemicStatus.VERIFIED.value:    1.0,
    EpistemicStatus.PLAUSIBLE.value:   0.8,
    EpistemicStatus.HEURISTIC.value:   0.5,
    EpistemicStatus.UNRESOLVED.value:  0.5,
    EpistemicStatus.SPECULATIVE.value: 0.2,
    EpistemicStatus.REJECTED.value:    0.0,
}


def recoverability_index() -> float:
    rows = governed_hypotheses()
    if not rows:
        return 0.0
    scores = [
        _RECOVERABILITY_SCORE[r.detected_status]
        for r in rows
    ]
    return round(
        sum(scores) / len(scores), 6,
    )


def recoverable_share() -> float:
    """Fraction of hypotheses scoring >= 0.5
    on the recoverability scale."""
    rows = governed_hypotheses()
    if not rows:
        return 0.0
    ok = sum(
        1 for r in rows
        if _RECOVERABILITY_SCORE[
            r.detected_status
        ] >= 0.5
    )
    return round(ok / len(rows), 6)


__all__ = [
    "recoverability_index",
    "recoverable_share",
]
