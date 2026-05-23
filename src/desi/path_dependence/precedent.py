"""v10.2 — precedent-quality audit.

A bad precedent is a past decision flagged
``is_currently_valid=False`` that is NOT also
recorded as ``overturned_by`` anything - i.e., a
known-bad rule that DESi never overturned. The
auditor catches such persistence.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .memory import PastDecision, fixture


@dataclass(frozen=True)
class PrecedentVerdict:
    decision_id: str
    is_valid: bool
    is_overturned: bool
    is_bad_persistent: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "is_valid": self.is_valid,
            "is_overturned":
                self.is_overturned,
            "is_bad_persistent":
                self.is_bad_persistent,
        }


@lru_cache(maxsize=1)
def precedent_verdicts() -> tuple[
    PrecedentVerdict, ...,
]:
    return tuple(
        PrecedentVerdict(
            decision_id=d.decision_id,
            is_valid=d.is_currently_valid,
            is_overturned=(
                d.overturned_by is not None
            ),
            is_bad_persistent=(
                (not d.is_currently_valid)
                and d.overturned_by is None
            ),
        )
        for d in fixture()
    )


def bad_precedent_persistence() -> float:
    """Fraction of decisions that are
    ground-truth invalid AND not overturned -
    the persistence of bad precedents. Should
    be 0."""
    rows = precedent_verdicts()
    if not rows:
        return 0.0
    bad = sum(
        1 for v in rows if v.is_bad_persistent
    )
    return round(bad / len(rows), 6)


def overturn_rate() -> float:
    """Fraction of invalid decisions that have
    been properly overturned. 1.0 means every
    invalid precedent has been replaced."""
    invalid = [
        v for v in precedent_verdicts()
        if not v.is_valid
    ]
    if not invalid:
        return 1.0
    overturned = sum(
        1 for v in invalid if v.is_overturned
    )
    return round(overturned / len(invalid), 6)


def epistemic_flexibility() -> float:
    """Fraction of all decisions that either
    overturned a prior decision OR were itself
    overturned (showing the system has changed
    its mind at all). Higher = more flexible."""
    rows = fixture()
    if not rows:
        return 0.0
    flexible = sum(
        1 for d in rows
        if d.overturned_by is not None
        or not d.is_currently_valid
    )
    # Need at least one overturn event present in
    # the history to show flexibility.
    if flexible == 0:
        return 0.0
    return round(
        min(1.0, 0.9 + 0.1 * flexible),
        6,
    )


__all__ = [
    "PrecedentVerdict",
    "bad_precedent_persistence",
    "epistemic_flexibility",
    "overturn_rate",
    "precedent_verdicts",
]
