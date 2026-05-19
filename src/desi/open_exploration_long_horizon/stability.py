"""v12.3 — stability + drift metrics over the
5000-step long-horizon trajectory."""
from __future__ import annotations

from collections import Counter

from .mutation_governance import SHORT_WINDOW
from .trajectory import trajectory


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _distribution(steps: tuple) -> dict[
    str, float,
]:
    cnt = Counter(s.status for s in steps)
    total = sum(cnt.values())
    if total == 0:
        return {}
    return {
        k: cnt[k] / total
        for k in sorted(cnt.keys())
    }


def drift_growth() -> float:
    """Total-variation distance between the
    early-window and late-window status
    distributions. 0 means stable."""
    early = _distribution(
        trajectory()[:SHORT_WINDOW],
    )
    late = _distribution(
        trajectory()[-SHORT_WINDOW:],
    )
    keys = set(early) | set(late)
    if not keys:
        return 0.0
    tv = 0.5 * sum(
        abs(
            early.get(k, 0.0)
            - late.get(k, 0.0),
        )
        for k in keys
    )
    return _round(tv)


def exploration_productivity() -> float:
    """Fraction of late-window steps whose
    status is in {VERIFIED, PLAUSIBLE,
    HEURISTIC} - the "productive" labels.
    Stays close to its early-window value if
    DESi keeps exploring productively."""
    late = trajectory()[-SHORT_WINDOW:]
    if not late:
        return 0.0
    productive = sum(
        1 for s in late
        if s.status in {
            "verified", "plausible",
            "heuristic",
        }
    )
    return _round(productive / len(late))


def replay_stability() -> float:
    from .lineage import (
        lineage_replayed_identical,
    )
    return (
        1.0
        if lineage_replayed_identical()
        else 0.0
    )


__all__ = [
    "drift_growth",
    "exploration_productivity",
    "replay_stability",
]
