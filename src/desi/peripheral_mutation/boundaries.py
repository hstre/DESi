"""v31.0 - mutation boundaries.

Declares the allowed evolution space (peripheral infrastructure
areas) and enforces the boundary: a target is either an allowed
peripheral area or it touches the protected core (forbidden).
"""
from __future__ import annotations

from .protected_core import is_protected_core

# The areas DESi may mutate (peripheral infrastructure only).
ALLOWED_EVOLUTION_SPACE: tuple[str, ...] = (
    "replay_cache",
    "memoization",
    "graph_queries",
    "claim_extraction",
    "scientific_rendering",
    "citation_governance",
    "output_ports",
    "harvester_layer",
    "neo4j_projection",
    "evolution_memory_queries",
    "branch_ecology_visualization",
    "runtime_scheduling",
    "artifact_compression",
    "provenance_rendering",
)
_ALLOWED: frozenset[str] = frozenset(ALLOWED_EVOLUTION_SPACE)

BOUNDARY_ALLOWED = "allowed"
BOUNDARY_FORBIDDEN_CORE = "forbidden_core"


def is_allowed(area: str) -> bool:
    return area in _ALLOWED and not is_protected_core(area)


def classify_boundary(area: str) -> str:
    if is_protected_core(area):
        return BOUNDARY_FORBIDDEN_CORE
    if area in _ALLOWED:
        return BOUNDARY_ALLOWED
    return BOUNDARY_FORBIDDEN_CORE


__all__ = [
    "ALLOWED_EVOLUTION_SPACE",
    "BOUNDARY_ALLOWED",
    "BOUNDARY_FORBIDDEN_CORE",
    "classify_boundary",
    "is_allowed",
]
