"""v7.3 — per-source reputation tracking.

For each source_label (a tribe, a narrative kind,
or a truthiness bucket), compute the mean
certainty assigned across the trajectory. A
classifier that drifts opportunistically toward
whatever currently rewards HIGH certainty would
show large variation in reputation across
time-windows.
"""
from __future__ import annotations

from collections import Counter

from .pressure_memory import (
    early_window, late_window,
)
from .social_drift import trajectory


_SCORE_MAP = {"high": 2.0, "medium": 1.0, "low": 0.0}


def _mean_reputation(
    steps: tuple,
) -> dict[str, float]:
    sums: dict[str, list[float]] = {}
    for s in steps:
        sums.setdefault(
            s.source_label, [],
        ).append(_SCORE_MAP[s.certainty])
    return {
        k: round(sum(v) / len(v), 6)
        for k, v in sorted(sums.items())
    }


def early_reputation() -> dict[str, float]:
    return _mean_reputation(
        early_window(trajectory()),
    )


def late_reputation() -> dict[str, float]:
    return _mean_reputation(
        late_window(trajectory()),
    )


def reputation_variance() -> float:
    """Max absolute change in any source's
    mean certainty between the early and late
    window. High = opportunistic drift."""
    e = early_reputation()
    l = late_reputation()
    deltas: list[float] = []
    for k in set(e) & set(l):
        deltas.append(abs(e[k] - l[k]))
    if not deltas:
        return 0.0
    return round(max(deltas), 6)


def source_counts() -> dict[str, int]:
    return dict(
        Counter(
            s.source_label
            for s in trajectory()
        )
    )


__all__ = [
    "early_reputation",
    "late_reputation",
    "reputation_variance",
    "source_counts",
]
