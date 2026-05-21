"""v30.4 - closed A-E taxonomy for the evolution-memory verdict.

A-C are acceptable landings (replay-governed memory, stable
branch ecology, or productive but drifting); D and E are failures
(optimization-trapped or epistemically unstable).
"""
from __future__ import annotations

from enum import Enum


class EvolutionClass(Enum):
    A_REPLAY_GOVERNED_MEMORY = "replay_governed_evolutionary_memory"
    B_STABLE_BRANCH_ECOLOGY = "stable_branch_ecology"
    C_PRODUCTIVE_DRIFTING = "productive_but_drifting"
    D_OPTIMIZATION_TRAPPED = "optimization_trapped"
    E_EPISTEMICALLY_UNSTABLE = "epistemically_unstable"


EVOLUTION_CLASSES: tuple[str, ...] = tuple(
    c.value for c in EvolutionClass
)

_RANK: dict[str, int] = {
    EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value: 5,
    EvolutionClass.B_STABLE_BRANCH_ECOLOGY.value: 4,
    EvolutionClass.C_PRODUCTIVE_DRIFTING.value: 3,
    EvolutionClass.D_OPTIMIZATION_TRAPPED.value: 2,
    EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value: 1,
}

_MEANING: dict[str, str] = {
    EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value:
        "evolution history is replay-validated, governance-"
        "preserved, lineage-intact, risk-visible and human-gated "
        "- the strongest landing",
    EvolutionClass.B_STABLE_BRANCH_ECOLOGY.value:
        "branch ecology is stable but not fully replay-governed "
        "memory",
    EvolutionClass.C_PRODUCTIVE_DRIFTING.value:
        "evolution is productive but lineage or governance shows "
        "drift",
    EvolutionClass.D_OPTIMIZATION_TRAPPED.value:
        "evolution collapsed into a narrow optimisation trap - a "
        "failure",
    EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value:
        "replay or traceability broke - a failure",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value,
    EvolutionClass.B_STABLE_BRANCH_ECOLOGY.value,
    EvolutionClass.C_PRODUCTIVE_DRIFTING.value,
})


def class_rank(value: str) -> int:
    if value not in _RANK:
        raise KeyError(value)
    return _RANK[value]


def class_meaning(value: str) -> str:
    if value not in _MEANING:
        raise KeyError(value)
    return _MEANING[value]


def is_acceptable(value: str) -> bool:
    return value in _ACCEPTABLE


__all__ = [
    "EVOLUTION_CLASSES",
    "EvolutionClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
