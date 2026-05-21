"""v30.1 - risk memory.

Records every risk that blocked a rejected mutation as a
traceable occurrence, and clusters occurrences by risk type.
This is descriptive history only - marking risks, never blocking
future ideas.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.evolution_memory import decision_for, rejected_mutations


@dataclass(frozen=True)
class RiskOccurrence:
    occurrence_id: str
    mutation_id: str
    risk_type: str
    invariant: str
    agent: str

    def to_dict(self) -> dict[str, object]:
        return {
            "occurrence_id": self.occurrence_id,
            "mutation_id": self.mutation_id,
            "risk_type": self.risk_type,
            "invariant": self.invariant,
            "agent": self.agent,
        }


def risk_occurrences() -> tuple[RiskOccurrence, ...]:
    out: list[RiskOccurrence] = []
    for m in rejected_mutations():
        d = decision_for(m.mutation_id)
        out.append(RiskOccurrence(
            occurrence_id=f"RO_{m.mutation_id}",
            mutation_id=m.mutation_id,
            risk_type=d.reason,
            invariant=d.invariant,
            agent=m.proposed_by,
        ))
    return tuple(sorted(out, key=lambda o: o.occurrence_id))


def risk_clusters() -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for o in risk_occurrences():
        out.setdefault(o.risk_type, []).append(o.mutation_id)
    return {k: tuple(sorted(out[k])) for k in sorted(out)}


def risk_types() -> tuple[str, ...]:
    return tuple(sorted(risk_clusters()))


__all__ = [
    "RiskOccurrence",
    "risk_clusters",
    "risk_occurrences",
    "risk_types",
]
