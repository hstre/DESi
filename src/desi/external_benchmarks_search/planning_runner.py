"""v35.2 - planning-efficiency view over the real ToolChain branches.

Computes the search/planning reduction metrics from the real
connector branches: node reduction, compute reduction and branch
compression. A baseline recomputes every branch once; reuse and merge
cost nothing, and soft-reweighted branches stay as distinct nodes.
"""
from __future__ import annotations

from desi.benchmark_api_search import MODE_KEPT

from .toolchain_runner import real_branches, total_branches


def distinct_nodes() -> int:
    return sum(1 for b in real_branches() if b.recomputed)


def node_reduction() -> float:
    total = total_branches()
    if total <= 0:
        return 0.0
    return round((total - distinct_nodes()) / total, 6)


def compute_reduction() -> float:
    total = total_branches()
    if total <= 0:
        return 0.0
    recomputed = sum(1 for b in real_branches() if b.recomputed)
    return round((total - recomputed) / total, 6)


def branch_compression() -> float:
    total = total_branches()
    if total <= 0:
        return 0.0
    compressed = sum(
        1 for b in real_branches() if b.mode != MODE_KEPT
    )
    return round(compressed / total, 6)


__all__ = [
    "branch_compression",
    "compute_reduction",
    "distinct_nodes",
    "node_reduction",
]
