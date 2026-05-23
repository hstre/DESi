"""v8.0 — scarcity-aware claim scheduler.

The scheduler processes claims under a fixed
total budget. The closed Decision enum is
PROCESS / DEFER / SKIP - there is no
QUIETLY_DROP. A CORRECT scheduler sorts by
``epistemic_value`` descending and processes
within the budget; cost is only consulted to
check whether the remaining budget admits the
next claim. The cheap-but-low-value claims are
deliberately NOT favored - that would be
``resource_bias``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .resources import (
    ScarcityClaim, fixture,
)


BUDGET: float = 3.0


class ScheduleDecision(str, Enum):
    PROCESS = "process"
    DEFER   = "defer"
    SKIP    = "skip"


SCHEDULE_DECISIONS: tuple[str, ...] = tuple(
    d.value for d in ScheduleDecision
)


@dataclass(frozen=True)
class ScheduledClaim:
    claim_id: str
    complexity_cost: float
    epistemic_value: float
    decision: str
    running_cost: float

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "complexity_cost":
                self.complexity_cost,
            "epistemic_value":
                self.epistemic_value,
            "decision": self.decision,
            "running_cost":
                self.running_cost,
        }


@lru_cache(maxsize=1)
def schedule() -> tuple[ScheduledClaim, ...]:
    # Sort by epistemic_value desc, then by
    # complexity_cost asc as a stable secondary
    # tiebreaker (the cheap tiebreak is
    # consciously chosen and limited to ties).
    ranked = sorted(
        fixture(),
        key=lambda c: (
            -c.epistemic_value,
            c.complexity_cost,
            c.claim_id,
        ),
    )
    out: list[ScheduledClaim] = []
    used = 0.0
    for c in ranked:
        if used + c.complexity_cost <= BUDGET:
            d = ScheduleDecision.PROCESS.value
            used = round(
                used + c.complexity_cost, 6,
            )
        elif c.epistemic_value >= 0.40:
            d = ScheduleDecision.DEFER.value
        else:
            d = ScheduleDecision.SKIP.value
        out.append(ScheduledClaim(
            claim_id=c.claim_id,
            complexity_cost=c.complexity_cost,
            epistemic_value=c.epistemic_value,
            decision=d,
            running_cost=used,
        ))
    out.sort(key=lambda x: x.claim_id)
    return tuple(out)


def total_processed_cost() -> float:
    return round(sum(
        s.complexity_cost for s in schedule()
        if s.decision == (
            ScheduleDecision.PROCESS.value
        )
    ), 6)


def processed_count() -> int:
    return sum(
        1 for s in schedule()
        if s.decision == (
            ScheduleDecision.PROCESS.value
        )
    )


def deferred_count() -> int:
    return sum(
        1 for s in schedule()
        if s.decision == (
            ScheduleDecision.DEFER.value
        )
    )


def skipped_count() -> int:
    return sum(
        1 for s in schedule()
        if s.decision == (
            ScheduleDecision.SKIP.value
        )
    )


__all__ = [
    "BUDGET",
    "SCHEDULE_DECISIONS",
    "ScheduleDecision",
    "ScheduledClaim",
    "deferred_count",
    "processed_count",
    "schedule",
    "skipped_count",
    "total_processed_cost",
]
