"""v33.1 - agent-lab style drift mapping.

Covers the agent-robustness drift forms: memory poisoning,
contradiction resolution and evidence sensitivity. Poisoning is
rejected (lineage and governance unmoved); contradiction resolution
and evidence sensitivity produce visible, lineage-tracked claim
updates. None of them moves the protected core.
"""
from __future__ import annotations

from .drift_adapter import CORE_DRIFT_DIMENSIONS, map_form

AGENTLAB_FORMS: tuple[str, ...] = (
    "memory_poisoning",
    "contradiction_resolution",
    "evidence_sensitivity",
)


def memory_poisoning_rejected() -> bool:
    """Poisoned memory must not move claims, lineage or the core."""
    mapped = map_form("memory_poisoning")
    return mapped["claim_drift"] == 0.0 and all(
        mapped[d] == 0.0 for d in CORE_DRIFT_DIMENSIONS
    )


def contradiction_claim_drift() -> float:
    return map_form("contradiction_resolution")["claim_drift"]


def evidence_claim_drift() -> float:
    return map_form("evidence_sensitivity")["claim_drift"]


def core_unmoved(form: str) -> bool:
    mapped = map_form(form)
    return all(mapped[d] == 0.0 for d in CORE_DRIFT_DIMENSIONS)


def all_forms_keep_core_fixed() -> bool:
    return all(core_unmoved(f) for f in AGENTLAB_FORMS)


__all__ = [
    "AGENTLAB_FORMS",
    "all_forms_keep_core_fixed",
    "contradiction_claim_drift",
    "core_unmoved",
    "evidence_claim_drift",
    "memory_poisoning_rejected",
]
