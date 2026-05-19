"""v11.3 — efficiency aggregates."""
from __future__ import annotations

from ..desi_guided_search.search_budget import (
    baseline_node_count, guided_node_count,
)
from ..tactical_stress.trap_detection import (
    critical_line_preservation,
    tactical_miss_rate,
)
from .costs import (
    baseline_energy, baseline_time_ms,
    guided_energy, guided_time_ms,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def compute_reduction() -> float:
    """Mean reduction across (nodes, time,
    energy)."""
    base_n = baseline_node_count()
    guid_n = guided_node_count()
    base_t = baseline_time_ms()
    guid_t = guided_time_ms()
    base_e = baseline_energy()
    guid_e = guided_energy()
    reductions = []
    for base, guid in (
        (base_n, guid_n),
        (base_t, guid_t),
        (base_e, guid_e),
    ):
        if base > 0:
            reductions.append(
                (base - guid) / base,
            )
    if not reductions:
        return 0.0
    return _round(
        sum(reductions) / len(reductions),
    )


def elo_delta_proxy() -> float:
    """Synthetic Elo delta proxy. v11.2 shows
    DESi misses zero tactical cases; so the
    playing-strength delta is a small negative
    perturbation proportional to tactical_miss_
    rate. Clipped negative is BAD; we report
    raw."""
    miss = tactical_miss_rate()
    # 100 Elo per 10 percent miss rate (a
    # synthetic conversion factor) - if miss
    # rate is 0 the delta is 0.
    return _round(-1000.0 * miss)


def quality_preservation() -> float:
    """Composite: critical_line_preservation
    weighted equally with (1 - tactical_miss).
    """
    clp = critical_line_preservation()
    miss = tactical_miss_rate()
    return _round((clp + (1.0 - miss)) / 2.0)


def branch_compression() -> float:
    """Compression ratio = 1 - guided_nodes /
    baseline_nodes."""
    base = baseline_node_count()
    if base == 0:
        return 0.0
    return _round(
        1.0 - guided_node_count() / base,
    )


__all__ = [
    "branch_compression",
    "compute_reduction",
    "elo_delta_proxy",
    "quality_preservation",
]
