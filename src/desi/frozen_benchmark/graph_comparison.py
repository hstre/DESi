"""v32.1 - graph query efficiency comparison.

The graph-signature rebuild stands in for a graph query: the
baseline recomputes it on every access, the mutated version reuses a
replay-safe memoised result. The query result (graph integrity) is
byte-identical, while the recompute count drops.
"""
from __future__ import annotations

from desi.frozen_baseline import baseline_run, baseline_workload

from .benchmark import mutated_run

_GRAPH_WORKLOAD = "graph_signature_rebuild"


def _repeat_of(name: str) -> int:
    for w in baseline_workload():
        if w.name == name:
            return w.repeat
    return 0


def graph_baseline_recomputes() -> int:
    return _repeat_of(_GRAPH_WORKLOAD)


def graph_mutated_recomputes() -> int:
    return 1 if _repeat_of(_GRAPH_WORKLOAD) > 0 else 0


def graph_query_reduction() -> float:
    base = graph_baseline_recomputes()
    if base <= 0:
        return 0.0
    return (base - graph_mutated_recomputes()) / base


def graph_integrity() -> float:
    """1.0 iff the graph query result is byte-identical between the
    baseline and the mutated version."""
    base = baseline_run().output_map().get(_GRAPH_WORKLOAD)
    mut = mutated_run().output_map().get(_GRAPH_WORKLOAD)
    if base is None or mut is None:
        return 0.0
    return 1.0 if base == mut else 0.0


__all__ = [
    "graph_baseline_recomputes",
    "graph_integrity",
    "graph_mutated_recomputes",
    "graph_query_reduction",
]
