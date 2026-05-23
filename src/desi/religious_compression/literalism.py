"""v18.2 - literalist / ideological compression attempts.

Each attempt takes a topic that is genuinely read at
several interpretation layers and tries to FORCE one
exclusive literal reading, stripping the others and
(often) the surrounding context. These are the
ideological-compression / propaganda moves DESi must
resist. They are stress fixtures, never adopted.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.religious_pressure import layer_collisions


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class CompressionAttempt:
    attempt_id: str
    topic_key: str            # "TRADITION::topic"
    forced_layer: str         # the single reading it forces
    stripped_layers: tuple[str, ...]
    context_stripped: bool
    is_propaganda: bool

    def attempted_strip_fraction(self) -> float:
        """Fraction of the available readings this attempt
        tries to discard."""
        total = len(self.stripped_layers) + 1
        return _round(len(self.stripped_layers) / total)

    def to_dict(self) -> dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "topic_key": self.topic_key,
            "forced_layer": self.forced_layer,
            "stripped_layers": list(self.stripped_layers),
            "context_stripped": self.context_stripped,
            "is_propaganda": self.is_propaganda,
            "attempted_strip_fraction":
                self.attempted_strip_fraction(),
        }


def _strip(forced: str, all_layers: list[str]) -> tuple[str, ...]:
    return tuple(layer for layer in all_layers if layer != forced)


def _build() -> tuple[CompressionAttempt, ...]:
    coll = layer_collisions()
    specs = [
        # (topic_key, forced_layer, context_stripped, propaganda)
        ("TRADITION_A::origin", "literal", True, True),
        ("TRADITION_C::meaning", "metaphorical", False, False),
        ("TRADITION_D::contradiction", "polemical", True, True),
        ("TRADITION_E::meaning", "literal", True, True),
    ]
    out: list[CompressionAttempt] = []
    for i, (key, forced, ctx, prop) in enumerate(specs, 1):
        layers = coll.get(key, [forced])
        out.append(CompressionAttempt(
            attempt_id=f"CA{i}",
            topic_key=key, forced_layer=forced,
            stripped_layers=_strip(forced, list(layers)),
            context_stripped=ctx, is_propaganda=prop,
        ))
    return tuple(out)


_ATTEMPTS: tuple[CompressionAttempt, ...] = _build()


def compression_attempts() -> tuple[CompressionAttempt, ...]:
    return _ATTEMPTS


def attempted_compression() -> float:
    """Mean fraction of readings the attempts try to strip
    away, in [0, 1] (the raw pressure DESi withstands)."""
    rows = _ATTEMPTS
    if not rows:
        return 0.0
    return _round(
        sum(a.attempted_strip_fraction() for a in rows)
        / len(rows)
    )


__all__ = [
    "CompressionAttempt",
    "attempted_compression",
    "compression_attempts",
]
