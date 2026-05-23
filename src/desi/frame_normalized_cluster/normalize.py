"""v3.90 — frame-normalized novel anchor vectors.

The v3.89 RESIDUAL projection is the canonical
"frame-normalized" representation; this module
re-exports it under a v3.90 name so the v3.86
clustering scaffolding can swap inputs without
peeking inside the v3.89 internals.
"""
from __future__ import annotations

from ..frame_normalization.contribution import (
    FrameCondition, novel_vectors_residual,
)


def frame_normalized_vectors() -> dict[
    str, tuple[float, ...],
]:
    return novel_vectors_residual()


__all__ = [
    "FrameCondition",
    "frame_normalized_vectors",
]
