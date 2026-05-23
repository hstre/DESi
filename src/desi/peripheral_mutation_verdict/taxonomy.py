"""v31.4 - closed A-E taxonomy for the peripheral mutation verdict.

A-C are acceptable landings (stable peripheral evolution, replay-safe
mutation, or productive but drifting); D and E are failures (hidden
core erosion or epistemically unstable).
"""
from __future__ import annotations

from enum import Enum


class MutationClass(Enum):
    A_STABLE_PERIPHERAL_EVOLUTION = "stable_peripheral_evolution"
    B_REPLAY_SAFE_MUTATION = "replay_safe_mutation"
    C_PRODUCTIVE_DRIFTING = "productive_but_drifting"
    D_HIDDEN_CORE_EROSION = "hidden_core_erosion"
    E_EPISTEMICALLY_UNSTABLE = "epistemically_unstable"


MUTATION_CLASSES: tuple[str, ...] = tuple(
    c.value for c in MutationClass
)

_RANK: dict[str, int] = {
    MutationClass.A_STABLE_PERIPHERAL_EVOLUTION.value: 5,
    MutationClass.B_REPLAY_SAFE_MUTATION.value: 4,
    MutationClass.C_PRODUCTIVE_DRIFTING.value: 3,
    MutationClass.D_HIDDEN_CORE_EROSION.value: 2,
    MutationClass.E_EPISTEMICALLY_UNSTABLE.value: 1,
}

_MEANING: dict[str, str] = {
    MutationClass.A_STABLE_PERIPHERAL_EVOLUTION.value:
        "real peripheral mutations are replay-validated, the "
        "protected core stays byte-identical, governance and "
        "lineage are intact, mutations are traceable and human-"
        "gated - the strongest landing",
    MutationClass.B_REPLAY_SAFE_MUTATION.value:
        "mutations are replay-safe and core-preserving but not yet "
        "a fully stable long-horizon evolution",
    MutationClass.C_PRODUCTIVE_DRIFTING.value:
        "mutations are productive but lineage or governance shows "
        "drift",
    MutationClass.D_HIDDEN_CORE_EROSION.value:
        "the protected core changed under mutation - a failure",
    MutationClass.E_EPISTEMICALLY_UNSTABLE.value:
        "replay or mutation traceability broke - a failure",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    MutationClass.A_STABLE_PERIPHERAL_EVOLUTION.value,
    MutationClass.B_REPLAY_SAFE_MUTATION.value,
    MutationClass.C_PRODUCTIVE_DRIFTING.value,
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
    "MUTATION_CLASSES",
    "MutationClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
