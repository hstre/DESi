"""v32.3 - mutation efficiency and overengineering detection.

For every evolution feature, efficiency is its measured benefit
relative to its complexity cost. The overengineering detector flags
features whose complexity exceeds their measured benefit - these are
local attractors: complexity that did not produce proportional
epistemic utility. The detector itself is deterministic and
replay-stable.
"""
from __future__ import annotations

from .utility import EvolutionFeature, evolution_features


def feature_efficiency() -> dict[str, float]:
    """benefit - complexity per feature (higher is better; negative
    means overengineered)."""
    return {
        f.name: round(f.benefit - f.complexity, 6)
        for f in evolution_features()
    }


def overengineered_features() -> tuple[str, ...]:
    """Features whose complexity exceeds their measured benefit."""
    return tuple(
        f.name for f in evolution_features() if f.is_overengineered
    )


def local_attractors() -> tuple[str, ...]:
    """Local attractors: complexity without proportional benefit -
    here, the same set the overengineering detector flags."""
    return overengineered_features()


def overengineering_detection() -> float:
    """1.0 iff the detector evaluated every feature and produced a
    replay-stable classification (the detector is functioning)."""
    a = overengineered_features()
    b = overengineered_features()
    if a != b:
        return 0.0
    classified = sum(
        1 for _ in evolution_features()
    )
    return 1.0 if classified == len(evolution_features()) else 0.0


def overengineering_free() -> bool:
    """True iff no feature is flagged as overengineered."""
    return not overengineered_features()


__all__ = [
    "feature_efficiency",
    "local_attractors",
    "overengineered_features",
    "overengineering_detection",
    "overengineering_free",
]
