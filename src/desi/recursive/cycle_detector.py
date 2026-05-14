"""Cycle detection — INV-R4: a cycle must never silently truncate.

The resolver tracks an *ancestor path* (root → … → current) as a
tuple of node ids. A cycle is detected the moment the next node id
the resolver wants to enter is already in that ancestor path.

The detector returns the full cycle (ancestors + the would-be
child) so that the ledger and the result carry an inspectable
explanation, not a silent truncation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CycleHit:
    """A detected cycle in the recursion."""

    cycle_path: tuple[str, ...]
    repeated_node: str

    def to_dict(self) -> dict:
        return {
            "cycle_path": list(self.cycle_path),
            "repeated_node": self.repeated_node,
        }


def check_for_cycle(
    next_node_id: str,
    ancestor_path: tuple[str, ...],
) -> CycleHit | None:
    """Return a :class:`CycleHit` if entering ``next_node_id`` would
    revisit any ancestor in ``ancestor_path``; otherwise ``None``.
    """
    if next_node_id in ancestor_path:
        return CycleHit(
            cycle_path=ancestor_path + (next_node_id,),
            repeated_node=next_node_id,
        )
    return None


__all__ = [
    "CycleHit",
    "check_for_cycle",
]
