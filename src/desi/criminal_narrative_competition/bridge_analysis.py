"""v16.1 - bridge pressure per narrative.

bridge_pressure is the fraction of a narrative's
inferential bridges that are UNSUPPORTED leaps.
High pressure means the narrative leans on many
inferences the public record does not back - a
structural observation, NEVER a verdict that the
narrative is false.
"""
from __future__ import annotations

from .narratives import Narrative, narratives


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def bridge_pressure_narrative(n: Narrative) -> float:
    if not n.bridges:
        return 0.0
    unsupported = sum(
        1 for b in n.bridges if not b.supported
    )
    return _round(unsupported / len(n.bridges))


def bridge_pressure_by_narrative() -> dict[str, float]:
    return {
        n.narrative_id: bridge_pressure_narrative(n)
        for n in narratives()
    }


def bridge_pressure() -> float:
    """Corpus-level: the MAXIMUM bridge pressure
    across narratives (the most leap-dependent
    framing), in [0, 1]."""
    by = bridge_pressure_by_narrative()
    if not by:
        return 0.0
    return _round(max(by.values()))


def most_bridge_dependent() -> str:
    """The narrative needing the most unsupported
    bridges (Pflichtfrage 1). Ties broken
    lexicographically for determinism."""
    by = bridge_pressure_by_narrative()
    return max(
        sorted(by), key=lambda k: by[k],
    )


__all__ = [
    "bridge_pressure",
    "bridge_pressure_by_narrative",
    "bridge_pressure_narrative",
    "most_bridge_dependent",
]
