"""v34.2 - per-dimension determinism scorecard.

Records, for every reproducibility dimension, the shared signature
and whether it stayed identical across all repeats.
"""
from __future__ import annotations

from dataclasses import dataclass

from .artifact_identity import (
    artifact_identity, citation_identity, metric_identity,
    output_identity, replay_hash_identity, section_identity,
)
from .repro_runner import snapshot


@dataclass(frozen=True)
class DeterminismCard:
    dimension: str
    signature: str
    identical: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "dimension": self.dimension,
            "signature": self.signature,
            "identical": self.identical,
        }


_DIMS = (
    ("output_identity", "output", output_identity),
    ("metric_identity", "metric", metric_identity),
    ("citation_identity", "citation", citation_identity),
    ("section_identity", "section", section_identity),
    ("artifact_identity", "artifact", artifact_identity),
    ("replay_hash_identity", "replay", replay_hash_identity),
)


def determinism_scorecards() -> tuple[DeterminismCard, ...]:
    snap = snapshot()
    return tuple(
        DeterminismCard(
            dimension=name,
            signature=snap[key],
            identical=(fn() == 1.0),
        )
        for name, key, fn in _DIMS
    )


__all__ = [
    "DeterminismCard",
    "determinism_scorecards",
]
