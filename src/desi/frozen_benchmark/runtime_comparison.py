"""v32.1 - runtime comparison (recompute count + replay stability).

The recompute count is the deterministic, reproducible runtime
proxy. Wall-clock is observed live for information only and is never
stored, because it is non-deterministic across machines and runs.
"""
from __future__ import annotations

import time

from .benchmark import (
    baseline_recomputes, measured_improvement, mutated_recomputes,
    mutated_run,
)
from desi.frozen_baseline import baseline_run


def recompute_reduction() -> float:
    return measured_improvement()


def observe_wall_clock() -> dict[str, float]:
    """Observe live wall-clock for the two runs. For information
    only - NEVER stored in any artifact."""
    t0 = time.perf_counter()
    baseline_run()
    t1 = time.perf_counter()
    mutated_run()
    t2 = time.perf_counter()
    return {
        "baseline_seconds": t1 - t0,
        "mutated_seconds": t2 - t1,
    }


def replay_stability() -> float:
    """1.0 iff both runs reproduce identical recompute counts and
    outputs across recomputation."""
    if baseline_recomputes() != baseline_recomputes():
        return 0.0
    if mutated_recomputes() != mutated_recomputes():
        return 0.0
    if mutated_run().outputs != mutated_run().outputs:
        return 0.0
    if baseline_run().outputs != baseline_run().outputs:
        return 0.0
    return 1.0


__all__ = [
    "observe_wall_clock",
    "recompute_reduction",
    "replay_stability",
]
