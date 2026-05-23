"""v27.2 - shared research assumptions.

Maps which assumptions are shared across papers. A shared
assumption is a structural fact, not a judgement: DESi reports
that papers rest on a common assumption, never whether the
assumption is correct.
"""
from __future__ import annotations

from desi.research_harvester import all_assumptions, papers


def assumption_map() -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {}
    for p in papers():
        for a in p.assumptions:
            out.setdefault(a, []).append(p.paper_id)
    return {
        a: tuple(sorted(out[a])) for a in sorted(out)
    }


def shared_assumptions() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Assumptions held by at least two papers, sorted."""
    m = assumption_map()
    return tuple(
        (a, m[a]) for a in sorted(m) if len(m[a]) >= 2
    )


def assumption_count() -> int:
    return len(all_assumptions())


__all__ = [
    "assumption_count",
    "assumption_map",
    "shared_assumptions",
]
