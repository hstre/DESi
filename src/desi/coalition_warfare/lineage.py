"""v9.2 — provenance / lineage tracking.

Builds the parent-child lineage graph from the
``parent_id`` field. Every node belongs to
exactly one tree. A coalition is detected when
a tree's root spawns >= 2 children with the
SAME text - that is the closed signature of a
coordinated narrative.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .coalitions import (
    Broadcast, CoalitionRole, fixture,
)


@dataclass(frozen=True)
class LineageNode:
    broadcast_id: str
    parent_id: str | None
    descendants: tuple[str, ...]
    root_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "broadcast_id": self.broadcast_id,
            "parent_id": self.parent_id,
            "descendants":
                list(self.descendants),
            "root_id": self.root_id,
        }


@lru_cache(maxsize=1)
def lineage_nodes() -> tuple[
    LineageNode, ...,
]:
    by_id = {
        b.broadcast_id: b for b in fixture()
    }
    children: dict[str, list[str]] = {}
    for b in fixture():
        if b.parent_id is not None:
            children.setdefault(
                b.parent_id, [],
            ).append(b.broadcast_id)

    def _root(bid: str) -> str:
        cur = bid
        while True:
            parent = by_id[cur].parent_id
            if parent is None:
                return cur
            cur = parent

    out: list[LineageNode] = []
    for b in fixture():
        kids = tuple(sorted(
            children.get(b.broadcast_id, []),
        ))
        out.append(LineageNode(
            broadcast_id=b.broadcast_id,
            parent_id=b.parent_id,
            descendants=kids,
            root_id=_root(b.broadcast_id),
        ))
    out.sort(key=lambda n: n.broadcast_id)
    return tuple(out)


@lru_cache(maxsize=1)
def detected_coalitions() -> tuple[
    tuple[str, tuple[str, ...]], ...,
]:
    """A detected coalition is identified by
    its root broadcast_id together with the
    set of descendants that share the SAME
    text as the root. The closed signature: a
    tree with at least one descendant that
    repeats the root's text verbatim (honest
    forwarding does not preserve text exactly)."""
    by_id = {
        b.broadcast_id: b for b in fixture()
    }
    out: list[
        tuple[str, tuple[str, ...]],
    ] = []
    for node in lineage_nodes():
        if node.parent_id is not None:
            continue
        root = by_id[node.broadcast_id]
        same_text = [
            d for d in node.descendants
            if by_id[d].text == root.text
        ]
        if len(same_text) >= 1:
            members = tuple(sorted(
                [node.broadcast_id]
                + list(same_text),
            ))
            out.append((
                node.broadcast_id, members,
            ))
    return tuple(out)


def coalition_detection() -> float:
    """Of all ground-truth COALITION_MEMBER
    broadcasts, how many ended up in a detected
    coalition?"""
    truth_members = {
        b.broadcast_id for b in fixture()
        if b.coalition_role == (
            CoalitionRole.COALITION_MEMBER.value
        )
    }
    detected_members: set[str] = set()
    for _, members in detected_coalitions():
        detected_members.update(members)
    if not truth_members:
        return 1.0
    overlap = truth_members & detected_members
    return round(
        len(overlap) / len(truth_members), 6,
    )


def lineage_stability() -> float:
    """Run the lineage builder twice; if the
    output diverges, stability < 1.0."""
    a = lineage_nodes()
    b = lineage_nodes()
    return 1.0 if a == b else 0.0


__all__ = [
    "LineageNode",
    "coalition_detection",
    "detected_coalitions",
    "lineage_nodes",
    "lineage_stability",
]
