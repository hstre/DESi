"""Depth guard — INV against unbounded recursion.

``max_depth`` is counted from the root (depth=0). A bridge child of
the root sits at depth=1; a grandchild at depth=2; and so on.
``current_depth > max_depth`` triggers the
``RESOLUTION_DEPTH_EXCEEDED`` final state.

The default :data:`DEFAULT_MAX_DEPTH` is 3 — the same value the
v1.4 directive prescribes.
"""
from __future__ import annotations

from dataclasses import dataclass


DEFAULT_MAX_DEPTH: int = 3


@dataclass(frozen=True)
class DepthExceeded:
    """Marker payload for a depth-exceeded outcome."""

    current_depth: int
    max_depth: int

    def to_dict(self) -> dict:
        return {
            "current_depth": self.current_depth,
            "max_depth": self.max_depth,
        }


def check_depth(
    current_depth: int,
    max_depth: int,
) -> DepthExceeded | None:
    """Return a :class:`DepthExceeded` if the recursion has gone
    past the cap; otherwise ``None``.
    """
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    if current_depth > max_depth:
        return DepthExceeded(
            current_depth=current_depth, max_depth=max_depth,
        )
    return None


__all__ = [
    "DEFAULT_MAX_DEPTH",
    "DepthExceeded",
    "check_depth",
]
