"""v38.4 - closed A-E taxonomy for live LLM validation.

A and B are healthy landings (a live-validated epistemic governance
system, or a stable live-routing system); C is a warning (partially
robust); D and E are failures (live-unstable, or governance-unsafe).
"""
from __future__ import annotations

from enum import Enum


class LiveClass(Enum):
    A_LIVE_VALIDATED = "live_validated_epistemic_governance_system"
    B_STABLE_ROUTING = "stable_live_routing_system"
    C_PARTIALLY_ROBUST = "partially_robust"
    D_LIVE_UNSTABLE = "live_unstable"
    E_GOVERNANCE_UNSAFE = "governance_unsafe"


LIVE_CLASSES: tuple[str, ...] = tuple(c.value for c in LiveClass)

_RANK: dict[str, int] = {
    LiveClass.A_LIVE_VALIDATED.value: 5,
    LiveClass.B_STABLE_ROUTING.value: 4,
    LiveClass.C_PARTIALLY_ROBUST.value: 3,
    LiveClass.D_LIVE_UNSTABLE.value: 2,
    LiveClass.E_GOVERNANCE_UNSAFE.value: 1,
}

_MEANING: dict[str, str] = {
    LiveClass.A_LIVE_VALIDATED.value:
        "real OpenRouter LLM outputs (Granite + DeepSeek) are "
        "captured, replayed and graded under stable governance, with "
        "hallucinations contained and routing cost-effective - a "
        "live-validated epistemic governance system, the strongest "
        "landing",
    LiveClass.B_STABLE_ROUTING.value:
        "live routing and governance are stable, but one model score "
        "falls short of its full gate threshold",
    LiveClass.C_PARTIALLY_ROBUST.value:
        "some live dimensions pass while others miss their gate - "
        "partially robust",
    LiveClass.D_LIVE_UNSTABLE.value:
        "a live run was unstable or hallucination was not adequately "
        "contained - a failure",
    LiveClass.E_GOVERNANCE_UNSAFE.value:
        "governance identity or replay broke under live LLM outputs "
        "- governance-unsafe",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    LiveClass.A_LIVE_VALIDATED.value,
    LiveClass.B_STABLE_ROUTING.value,
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
    "LIVE_CLASSES",
    "LiveClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
