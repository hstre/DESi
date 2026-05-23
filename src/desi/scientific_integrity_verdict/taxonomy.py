"""v13.4 — closed scientific-integrity verdict
taxonomy."""
from __future__ import annotations

from enum import Enum


class ScientificIntegrityClass(str, Enum):
    EPISTEMICALLY_RIGOROUS      = (
        "A_epistemically_rigorous"
    )
    STRUCTURALLY_TRUSTWORTHY    = (
        "B_structurally_trustworthy"
    )
    PARTIALLY_RELIABLE          = (
        "C_partially_reliable"
    )
    EPISTEMICALLY_THIN          = (
        "D_epistemically_thin"
    )
    SLUDGE_COMPATIBLE_SYSTEM    = (
        "E_sludge_compatible_system"
    )


SCIENTIFIC_INTEGRITY_CLASSES: tuple[
    str, ...,
] = tuple(
    c.value for c in ScientificIntegrityClass
)


__all__ = [
    "SCIENTIFIC_INTEGRITY_CLASSES",
    "ScientificIntegrityClass",
]
