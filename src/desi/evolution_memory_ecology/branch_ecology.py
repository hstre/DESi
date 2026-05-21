"""v30.3 - branch ecology across generations.

Each generation forks a branch from the previous generation,
forming an acyclic lineage rooted at the sandbox base. No branch
is orphaned, none targets main, and the lineage is fully
traceable.
"""
from __future__ import annotations

from .generations import run

_SANDBOX_BASE = "sandbox_base"


def lineage_edges() -> tuple[tuple[str, str], ...]:
    """(branch, parent) edges across all generations."""
    return tuple(
        (r.branch_id, r.parent_branch) for r in run().records
    )


def orphan_branches() -> tuple[str, ...]:
    """Branches whose parent is neither the base nor an existing
    earlier branch - must be empty."""
    branches = {r.branch_id for r in run().records}
    known = branches | {_SANDBOX_BASE}
    return tuple(sorted(
        b for b, parent in lineage_edges() if parent not in known
    ))


def branches_targeting_main() -> tuple[str, ...]:
    return tuple(sorted(
        b for b, _ in lineage_edges() if b.endswith(":main")
        or b == "main"
    ))


def has_cycle() -> bool:
    parent = {b: p for b, p in lineage_edges()}
    for start in parent:
        seen = set()
        node = start
        while node in parent:
            if node in seen:
                return True
            seen.add(node)
            node = parent[node]
    return False


def branch_lineage_integrity() -> float:
    """1.0 iff no orphan branches, no cycle and none targets
    main."""
    checks = [
        not orphan_branches(),
        not has_cycle(),
        not branches_targeting_main(),
    ]
    return round(sum(1 for c in checks if c) / len(checks), 6)


__all__ = [
    "branch_lineage_integrity",
    "branches_targeting_main",
    "has_cycle",
    "lineage_edges",
    "orphan_branches",
]
