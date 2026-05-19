"""v8.4 — closed persistent-conflict-class
taxonomy. Five outcome classes. No fallback."""
from __future__ import annotations

from enum import Enum


class PersistentConflictClass(str, Enum):
    """Closed verdict space.

    * ``EPISTEMICALLY_RESILIENT``    - all 6
      Concept-Gate conditions pass.
    * ``BOUNDED_OPPORTUNISM``        - small
      opportunism observed but bounded.
    * ``PRESSURE_SENSITIVE``         - resource
      or reputation bias broke the ceiling.
    * ``GOVERNANCE_FRAGILE``         - governance
      fell below floor.
    * ``OPTIMIZATION_CORRUPTIBLE``   - replay
      collapse or goodhart_risk broke through.
    """
    EPISTEMICALLY_RESILIENT  = (
        "A_epistemically_resilient"
    )
    BOUNDED_OPPORTUNISM      = (
        "B_bounded_opportunism"
    )
    PRESSURE_SENSITIVE       = (
        "C_pressure_sensitive"
    )
    GOVERNANCE_FRAGILE       = (
        "D_governance_fragile"
    )
    OPTIMIZATION_CORRUPTIBLE = (
        "E_optimization_corruptible"
    )


PERSISTENT_CONFLICT_CLASSES: tuple[
    str, ...,
] = tuple(
    c.value for c in PersistentConflictClass
)


__all__ = [
    "PERSISTENT_CONFLICT_CLASSES",
    "PersistentConflictClass",
]
