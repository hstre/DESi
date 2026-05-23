"""v30.1 - the preserved rejection history.

Every rejected mutation stays in the history with its risk,
violated invariant and proposer. Nothing is deleted; each entry
is traceable to its mutation and decision.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.evolution_memory import (
    decision_for, rejected_mutations,
)

from .risk_memory import risk_occurrences


@dataclass(frozen=True)
class RejectionEntry:
    mutation_id: str
    risk_type: str
    invariant: str
    agent: str
    target_area: str

    def to_dict(self) -> dict[str, object]:
        return {
            "mutation_id": self.mutation_id,
            "risk_type": self.risk_type,
            "invariant": self.invariant,
            "agent": self.agent,
            "target_area": self.target_area,
        }


def rejection_history() -> tuple[RejectionEntry, ...]:
    out: list[RejectionEntry] = []
    for m in rejected_mutations():
        d = decision_for(m.mutation_id)
        out.append(RejectionEntry(
            mutation_id=m.mutation_id,
            risk_type=d.reason,
            invariant=d.invariant,
            agent=m.proposed_by,
            target_area=m.target_area,
        ))
    return tuple(sorted(out, key=lambda e: e.mutation_id))


def nothing_deleted() -> bool:
    """Every rejected mutation appears in the history."""
    rejected = {m.mutation_id for m in rejected_mutations()}
    recorded = {e.mutation_id for e in rejection_history()}
    return rejected == recorded


def risk_traceability() -> float:
    """Fraction of risk occurrences traceable to a recorded
    rejection entry (mutation + invariant), in [0, 1]."""
    occ = risk_occurrences()
    if not occ:
        return 1.0
    recorded = {e.mutation_id: e for e in rejection_history()}
    ok = 0
    for o in occ:
        e = recorded.get(o.mutation_id)
        if (
            e is not None
            and e.risk_type == o.risk_type
            and e.invariant == o.invariant
        ):
            ok += 1
    return round(ok / len(occ), 6)


__all__ = [
    "RejectionEntry",
    "nothing_deleted",
    "rejection_history",
    "risk_traceability",
]
