"""v25.4 - closed A-E taxonomy for the output-port verdict.

A-C are acceptable landings (publication-ready, traceable, or
format-stable); D and E are failures (citation-fragile or an
epistemically unsafe renderer).
"""
from __future__ import annotations

from enum import Enum


class PortClass(Enum):
    A_PUBLICATION_READY = "publication_ready_port_system"
    B_TRACEABLE = "traceable_output_system"
    C_FORMAT_STABLE_INCOMPLETE = "format_stable_but_incomplete"
    D_CITATION_FRAGILE = "citation_fragile"
    E_UNSAFE_RENDERER = "epistemically_unsafe_renderer"


PORT_CLASSES: tuple[str, ...] = tuple(
    c.value for c in PortClass
)

_RANK: dict[str, int] = {
    PortClass.A_PUBLICATION_READY.value: 5,
    PortClass.B_TRACEABLE.value: 4,
    PortClass.C_FORMAT_STABLE_INCOMPLETE.value: 3,
    PortClass.D_CITATION_FRAGILE.value: 2,
    PortClass.E_UNSAFE_RENDERER.value: 1,
}

_MEANING: dict[str, str] = {
    PortClass.A_PUBLICATION_READY.value:
        "schema-integral, citation-bound, fully traceable, "
        "cross-port consistent and replay-stable - the "
        "strongest landing",
    PortClass.B_TRACEABLE.value:
        "outputs are traceable but not fully cross-port "
        "consistent or publication-ready",
    PortClass.C_FORMAT_STABLE_INCOMPLETE.value:
        "formats are stable but some required structure or "
        "derivation is incomplete",
    PortClass.D_CITATION_FRAGILE.value:
        "citations are fragile (phantom, missing or "
        "misaligned) - a failure",
    PortClass.E_UNSAFE_RENDERER.value:
        "the renderer admits naked claims or forbidden output - "
        "a governance failure",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    PortClass.A_PUBLICATION_READY.value,
    PortClass.B_TRACEABLE.value,
    PortClass.C_FORMAT_STABLE_INCOMPLETE.value,
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
    "PORT_CLASSES",
    "PortClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
