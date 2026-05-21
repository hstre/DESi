"""v30.0 - decisions and their reasons.

Every mutation carries an explicit decision (ACCEPT / REJECT)
with a recorded reason: accepted ideas reference the evolution
metric that justified them; rejected ideas reference the risk
that blocked them and the invariant they would have violated.
"""
from __future__ import annotations

from dataclasses import dataclass

from .mutations import MutationIdea, mutations

DECISION_ACCEPT = "ACCEPT"
DECISION_REJECT = "REJECT"
DECISION_OUTCOMES: tuple[str, ...] = (DECISION_ACCEPT, DECISION_REJECT)

# Which safety invariant a forbidden/escalating idea would have
# violated.
_RISK_INVARIANT: dict[str, str] = {
    "forbidden_core_target": "protected_core_immutability",
    "authority_escalation": "no_hidden_authority",
    "test_disabling": "regression_integrity",
}


@dataclass(frozen=True)
class Decision:
    decision_id: str
    mutation_id: str
    outcome: str
    reason: str
    invariant: str

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "mutation_id": self.mutation_id,
            "outcome": self.outcome,
            "reason": self.reason,
            "invariant": self.invariant,
        }


def _decision_for(m: MutationIdea) -> Decision:
    if m.accepted:
        return Decision(
            decision_id=f"DEC_{m.mutation_id}",
            mutation_id=m.mutation_id,
            outcome=DECISION_ACCEPT,
            reason=m.evolution_metric or "governance_safe",
            invariant="",
        )
    return Decision(
        decision_id=f"DEC_{m.mutation_id}",
        mutation_id=m.mutation_id,
        outcome=DECISION_REJECT,
        reason=m.risk or "unsafe",
        invariant=_RISK_INVARIANT.get(m.risk, "safety_invariant"),
    )


def decisions() -> tuple[Decision, ...]:
    return tuple(_decision_for(m) for m in mutations())


def decision_for(mutation_id: str) -> Decision:
    for d in decisions():
        if d.mutation_id == mutation_id:
            return d
    raise KeyError(mutation_id)


def risks() -> tuple[str, ...]:
    return tuple(sorted({
        d.reason for d in decisions()
        if d.outcome == DECISION_REJECT
    }))


def invariants() -> tuple[str, ...]:
    return tuple(sorted({
        d.invariant for d in decisions() if d.invariant
    }))


def evolution_metrics() -> tuple[str, ...]:
    return tuple(sorted({
        d.reason for d in decisions()
        if d.outcome == DECISION_ACCEPT
    }))


__all__ = [
    "DECISION_ACCEPT",
    "DECISION_OUTCOMES",
    "DECISION_REJECT",
    "Decision",
    "decision_for",
    "decisions",
    "evolution_metrics",
    "invariants",
    "risks",
]
