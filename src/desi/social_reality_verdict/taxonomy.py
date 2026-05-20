"""v7.4 — closed social-reality-class taxonomy.

Five outcome classes. No fallback, no synonyms.
"""
from __future__ import annotations

from enum import Enum


class SocialRealityClass(str, Enum):
    """Closed verdict space.

    * ``EPISTEMICALLY_RESILIENT``   - all 6
      Concept-Gate conditions pass.
    * ``BOUNDED_SOCIAL_DRIFT``      - drift
      stayed within an extended soft floor.
    * ``NARRATIVE_SUSCEPTIBLE``     - false-
      certainty or narrative-resistance failed.
    * ``POLARIZATION_UNSTABLE``     - identity
      bias too high.
    * ``EPISTEMICALLY_CORRUPTIBLE`` - governance
      eroded or virality bias broke through.
    """
    EPISTEMICALLY_RESILIENT  = (
        "A_epistemically_resilient"
    )
    BOUNDED_SOCIAL_DRIFT     = (
        "B_bounded_social_drift"
    )
    NARRATIVE_SUSCEPTIBLE    = (
        "C_narrative_susceptible"
    )
    POLARIZATION_UNSTABLE    = (
        "D_polarization_unstable"
    )
    EPISTEMICALLY_CORRUPTIBLE = (
        "E_epistemically_corruptible"
    )


SOCIAL_REALITY_CLASSES: tuple[str, ...] = tuple(
    c.value for c in SocialRealityClass
)


__all__ = [
    "SOCIAL_REALITY_CLASSES",
    "SocialRealityClass",
]
