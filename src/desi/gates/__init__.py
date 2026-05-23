"""desi.gates - stable facade for the Concept Gate.

    from desi.gates import concept_gate

Provides the shared closed six-condition gate structure and a
registry mapping each phase to its real, in-place gate_conditions().
"""
from __future__ import annotations

from . import concept_gate

__all__ = ["concept_gate"]
