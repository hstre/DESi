"""ResolutionReplay — INV-R1 in code.

The replay hash captures the full graph (sorted node ids + sorted
edge tuples) plus the final state. It does NOT depend on:

* recursion order (children may be resolved in any order)
* timestamp / wall-clock
* author / title / source / citation_count metadata
* the textual order of bridge tuples returned by the auditor

Two resolutions of the same input that walk the graph in different
orders produce identical ``replay_hash`` values.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ResolutionReplay:
    """Minimal record from which the replay hash is computed."""

    root_node_id: str
    sorted_node_ids: tuple[str, ...]
    sorted_edges: tuple[tuple[str, str], ...]
    final_state: str
    depth_reached: int

    @property
    def replay_hash(self) -> str:
        h = hashlib.sha256()
        h.update(self.root_node_id.encode("utf-8"))
        h.update(b"\x00")
        for nid in self.sorted_node_ids:
            h.update(nid.encode("utf-8"))
            h.update(b"\x00")
        h.update(b"\x01")
        for src, dst in self.sorted_edges:
            h.update(src.encode("utf-8"))
            h.update(b"\x00")
            h.update(dst.encode("utf-8"))
            h.update(b"\x00")
        h.update(b"\x02")
        h.update(self.final_state.encode("utf-8"))
        h.update(b"\x00")
        h.update(str(self.depth_reached).encode("utf-8"))
        return "rr_" + h.hexdigest()[:16]


__all__ = [
    "ResolutionReplay",
]
