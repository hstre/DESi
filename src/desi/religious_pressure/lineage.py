"""v18.0 - interpretation layers, layer collisions, and
historical layering.

A topic read at multiple interpretation layers (literal,
historical-critical, metaphorical, mystical, polemical)
is the normal, plural state of a living tradition. DESi
maps the layers and surfaces collisions (where layers
read the same topic differently) WITHOUT collapsing them
to one. Rich layering is a sign of preserved plurality.
"""
from __future__ import annotations

from .claims import (
    INTERPRETATION_LAYERS, claims,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _layers_by_topic() -> dict[tuple[str, str], set[str]]:
    out: dict[tuple[str, str], set[str]] = {}
    for c in claims():
        out.setdefault(
            (c.tradition, c.topic), set(),
        ).add(c.layer)
    return out


def layer_collisions() -> dict[str, list[str]]:
    """(tradition::topic) -> the >= 2 distinct layers
    reading it. Pflichtfrage 3: where layers collide."""
    out: dict[str, list[str]] = {}
    for (trad, topic), layers in _layers_by_topic().items():
        if len(layers) >= 2:
            out[f"{trad}::{topic}"] = sorted(layers)
    return dict(sorted(out.items()))


def distinct_layers_present() -> tuple[str, ...]:
    seen: set[str] = set()
    for c in claims():
        seen.add(c.layer)
    return tuple(sorted(seen))


def historical_layering() -> float:
    """Fraction of the closed layer set that the corpus
    actually exercises, in [0, 1]. High = rich, plural
    layering rather than a flattened single reading."""
    if not INTERPRETATION_LAYERS:
        return 0.0
    return _round(
        len(distinct_layers_present())
        / len(INTERPRETATION_LAYERS)
    )


def lineage_map() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for c in claims():
        out[c.claim_id] = {
            "tradition": c.tradition,
            "topic": c.topic,
            "layer": c.layer,
            "claim_type": c.claim_type,
        }
    return out


__all__ = [
    "distinct_layers_present",
    "historical_layering",
    "layer_collisions",
    "lineage_map",
]
