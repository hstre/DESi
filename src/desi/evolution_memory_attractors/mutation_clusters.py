"""v30.2 - mutation clusters.

Groups mutation ideas by the module/area they target and by the
agent that proposed them. Clustering is descriptive structure
over the evolution history; it ranks nothing.
"""
from __future__ import annotations

from desi.evolution_memory import mutations


def clusters_by_area() -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for m in mutations():
        out.setdefault(m.target_area, []).append(m.mutation_id)
    return {k: tuple(sorted(out[k])) for k in sorted(out)}


def clusters_by_agent() -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for m in mutations():
        out.setdefault(m.proposed_by, []).append(m.mutation_id)
    return {k: tuple(sorted(out[k])) for k in sorted(out)}


def clustered_mutations() -> frozenset[str]:
    seen: set[str] = set()
    for ms in clusters_by_area().values():
        seen.update(ms)
    return frozenset(seen)


def mutation_cluster_visibility() -> float:
    """Fraction of mutations placed in at least one cluster, in
    [0, 1]."""
    ms = mutations()
    if not ms:
        return 0.0
    placed = clustered_mutations()
    return round(
        sum(1 for m in ms if m.mutation_id in placed) / len(ms),
        6,
    )


__all__ = [
    "clusters_by_agent",
    "clusters_by_area",
    "clustered_mutations",
    "mutation_cluster_visibility",
]
