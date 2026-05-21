"""v31.3 - lineage of the 25 peripheral mutation generations.

Each generation forks one branch from its predecessor, forming a
single acyclic DESCENDS_FROM chain rooted at the proposal branch.
Lineage integrity means: every non-root branch has an existing
parent (orphan-free), the chain is acyclic (parents reference a
strictly earlier generation), and no branch descends from main.
"""
from __future__ import annotations

from dataclasses import dataclass

from .mutation_generations import run

EDGE_DESCENDS_FROM = "DESCENDS_FROM"


@dataclass(frozen=True)
class LineageEdge:
    child: str
    parent: str
    edge_type: str

    def to_dict(self) -> dict[str, object]:
        return {
            "child": self.child,
            "parent": self.parent,
            "edge_type": self.edge_type,
        }


def lineage_edges() -> tuple[LineageEdge, ...]:
    return tuple(
        LineageEdge(
            child=r.branch_id,
            parent=r.parent_branch,
            edge_type=EDGE_DESCENDS_FROM,
        )
        for r in run().records
    )


def branch_ids() -> tuple[str, ...]:
    return tuple(r.branch_id for r in run().records)


def root_branch() -> str:
    return run().records[0].parent_branch


def orphans() -> tuple[str, ...]:
    """Non-root children whose parent is neither the root branch
    nor an existing generation branch."""
    known = set(branch_ids())
    root = root_branch()
    out: list[str] = []
    for e in lineage_edges():
        if e.parent == root:
            continue
        if e.parent not in known:
            out.append(e.child)
    return tuple(out)


def is_acyclic() -> bool:
    """Parents always reference a strictly earlier generation, so
    the DESCENDS_FROM chain cannot contain a cycle."""
    index_of = {r.branch_id: r.index for r in run().records}
    root = root_branch()
    for e in lineage_edges():
        if e.parent == root:
            continue
        child_idx = index_of[e.child]
        parent_idx = index_of.get(e.parent)
        if parent_idx is None or parent_idx >= child_idx:
            return False
    return True


def targets_main() -> bool:
    """True if any branch in the lineage descends from main."""
    if "main" in {r.branch_id for r in run().records}:
        return True
    return any(r.targets_main for r in run().records)


def lineage_integrity() -> float:
    """1.0 iff the lineage is orphan-free, acyclic and never
    targets main."""
    ok = (
        not orphans()
        and is_acyclic()
        and not targets_main()
    )
    return 1.0 if ok else 0.0


__all__ = [
    "EDGE_DESCENDS_FROM",
    "LineageEdge",
    "branch_ids",
    "is_acyclic",
    "lineage_edges",
    "lineage_integrity",
    "orphans",
    "root_branch",
    "targets_main",
]
