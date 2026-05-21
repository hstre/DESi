"""v27.2 - methodological clusters.

Groups papers by shared method and by shared metric. A cluster
is a structural grouping - it carries no ordering and names no
preferred method.
"""
from __future__ import annotations

from desi.research_harvester import papers


def method_clusters() -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for p in papers():
        for m in p.methods:
            out.setdefault(m, []).append(p.paper_id)
    return {m: tuple(sorted(out[m])) for m in sorted(out)}


def metric_clusters() -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for p in papers():
        for mt in p.metrics:
            out.setdefault(mt, []).append(p.paper_id)
    return {mt: tuple(sorted(out[mt])) for mt in sorted(out)}


def shared_method_clusters() -> dict[str, tuple[str, ...]]:
    """Methods used by at least two papers (genuine clusters)."""
    return {
        m: ps for m, ps in method_clusters().items()
        if len(ps) >= 2
    }


def papers_in_a_method_cluster() -> frozenset[str]:
    seen: set[str] = set()
    for ps in method_clusters().values():
        seen.update(ps)
    return frozenset(seen)


def method_cluster_visibility() -> float:
    """Fraction of papers placed into at least one method
    cluster, in [0, 1]."""
    ps = papers()
    if not ps:
        return 0.0
    placed = papers_in_a_method_cluster()
    return round(
        sum(1 for p in ps if p.paper_id in placed) / len(ps), 6,
    )


__all__ = [
    "method_cluster_visibility",
    "method_clusters",
    "metric_clusters",
    "papers_in_a_method_cluster",
    "shared_method_clusters",
]
