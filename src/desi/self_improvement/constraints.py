"""v28.0 - self-improvement safety constraints.

The hard boundary of the sandbox. Some target areas are allowed
for improvement proposals; the protected core (replay kernel,
determinism scanner, concept gates, authority filters, governance
core, regression integrity, safety invariants) is forbidden - a
candidate touching it is UNSAFE and contained. Every change
requires human approval, without exception.
"""
from __future__ import annotations

from .improvement_taxonomy import ImprovementClass as I

# Human approval is mandatory for every proposed change. This is
# a constant invariant of the sandbox; nothing here auto-applies.
HUMAN_APPROVAL_REQUIRED: bool = True

# Allowed improvement target areas -> their improvement class.
_ALLOWED_TARGET_CLASS: dict[str, str] = {
    "replay_performance": I.PERFORMANCE.value,
    "memoization": I.CACHE.value,
    "graph_queries": I.GRAPH.value,
    "claim_extraction": I.EXTRACTION.value,
    "traceability": I.TRACEABILITY.value,
    "citation_governance": I.GOVERNANCE.value,
    "output_ports": I.RENDERING.value,
    "cache_strategies": I.CACHE.value,
    "scientific_rendering": I.RENDERING.value,
    "harvester_structure": I.EXTRACTION.value,
    "branch_testing": I.PERFORMANCE.value,
    "ecology_efficiency": I.EXPLORATION.value,
}

ALLOWED_TARGETS: tuple[str, ...] = tuple(
    sorted(_ALLOWED_TARGET_CLASS)
)

# The protected core - never an applicable improvement target.
FORBIDDEN_TARGETS: tuple[str, ...] = (
    "replay_kernel", "determinism_scanner", "concept_gates",
    "authority_filters", "governance_core",
    "regression_integrity", "safety_invariants",
)
_FORBIDDEN: frozenset[str] = frozenset(FORBIDDEN_TARGETS)
_ALLOWED: frozenset[str] = frozenset(ALLOWED_TARGETS)


def is_allowed_target(area: str) -> bool:
    return area in _ALLOWED


def is_forbidden_target(area: str) -> bool:
    return area in _FORBIDDEN


def is_safe_target(area: str) -> bool:
    return area in _ALLOWED and area not in _FORBIDDEN


def classify_target(area: str) -> str:
    """Improvement class for a target area; forbidden or unknown
    targets are UNSAFE."""
    if area in _ALLOWED and area not in _FORBIDDEN:
        return _ALLOWED_TARGET_CLASS[area]
    return I.UNSAFE.value


__all__ = [
    "ALLOWED_TARGETS",
    "FORBIDDEN_TARGETS",
    "HUMAN_APPROVAL_REQUIRED",
    "classify_target",
    "is_allowed_target",
    "is_forbidden_target",
    "is_safe_target",
]
