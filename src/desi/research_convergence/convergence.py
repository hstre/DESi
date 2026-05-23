"""v27.2 - claim convergence and emergent trends.

Two papers converge if they share any structural dimension - a
method, a metric, an assumption or a topic. Emergent trends are
reported purely as frequencies (how often a dimension recurs).
DESi observes trends; it never evaluates them, names a winner or
indicates a "right direction".
"""
from __future__ import annotations

from desi.research_harvester import papers


def _dimensions(p) -> frozenset[str]:
    dims: set[str] = set()
    dims.update(f"method:{m}" for m in p.methods)
    dims.update(f"metric:{m}" for m in p.metrics)
    dims.update(f"assumption:{a}" for a in p.assumptions)
    dims.update(f"topic:{t}" for t in p.metadata.categories)
    return frozenset(dims)


def shared_dimensions(a_id: str, b_id: str) -> tuple[str, ...]:
    by_id = {p.paper_id: p for p in papers()}
    return tuple(sorted(
        _dimensions(by_id[a_id]) & _dimensions(by_id[b_id])
    ))


def converging_papers() -> frozenset[str]:
    """Papers that share at least one structural dimension with
    another paper."""
    ps = papers()
    converging: set[str] = set()
    for i, p in enumerate(ps):
        for j, q in enumerate(ps):
            if i == j:
                continue
            if _dimensions(p) & _dimensions(q):
                converging.add(p.paper_id)
                break
    return frozenset(converging)


def convergence_visibility() -> float:
    """Fraction of papers participating in at least one
    convergence, in [0, 1]."""
    ps = papers()
    if not ps:
        return 0.0
    conv = converging_papers()
    return round(
        sum(1 for p in ps if p.paper_id in conv) / len(ps), 6,
    )


def emergent_trends() -> tuple[tuple[str, str, int], ...]:
    """Recurring dimensions reported as (kind, name, frequency).
    Frequency is a count, never a score or quality ordering."""
    counts: dict[tuple[str, str], int] = {}
    for p in papers():
        for m in p.methods:
            counts[("method", m)] = counts.get(("method", m), 0) + 1
        for a in p.assumptions:
            counts[("assumption", a)] = (
                counts.get(("assumption", a), 0) + 1
            )
        for t in p.metadata.categories:
            counts[("topic", t)] = counts.get(("topic", t), 0) + 1
    rows = [
        (kind, name, n)
        for (kind, name), n in counts.items()
        if n >= 2
    ]
    return tuple(sorted(rows, key=lambda r: (r[0], r[1])))


__all__ = [
    "convergence_visibility",
    "converging_papers",
    "emergent_trends",
    "shared_dimensions",
]
