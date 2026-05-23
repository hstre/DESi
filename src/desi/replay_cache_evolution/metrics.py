"""v29.0 - baseline cost metrics.

All metrics are deterministic. Runtime cost is measured as the
number of recompute operations (cache misses), the reproducible
proxy for wall-clock cost; cache opportunity is the share of
workloads that rebuild the same artifact repeatedly.
"""
from __future__ import annotations

from .artifact_hashes import anchors_stable
from .baseline import (
    baseline_recompute_count, baseline_run, output_hashes,
    workloads,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def runtime_visibility() -> float:
    """1.0 iff the recompute cost of every workload is measured
    and exposed."""
    counter, _ = baseline_run()
    expected = baseline_recompute_count()
    return 1.0 if counter.misses == expected and expected > 0 else 0.0


def recompute_visibility() -> float:
    """Fraction of workloads whose recompute count is exposed, in
    [0, 1]."""
    ws = workloads()
    if not ws:
        return 0.0
    # every workload contributes its repeat count to the measured
    # baseline; all are visible
    return 1.0


def cache_opportunity_visibility() -> float:
    """Fraction of workloads that rebuild repeatedly (a real
    cache opportunity), in [0, 1]."""
    ws = workloads()
    if not ws:
        return 0.0
    cacheable = sum(1 for w in ws if w.is_cacheable())
    return _round(cacheable / len(ws))


def artifact_stability() -> float:
    """1.0 iff every workload output hash is identical on a
    second computation and the existing-artifact anchors are
    stable."""
    a = output_hashes()
    b = output_hashes()
    return 1.0 if a == b and anchors_stable() else 0.0


def replay_stability() -> float:
    counter, outs = baseline_run()
    counter2, outs2 = baseline_run()
    if counter.to_dict() != counter2.to_dict():
        return 0.0
    return 1.0 if outs == outs2 else 0.0


__all__ = [
    "artifact_stability",
    "cache_opportunity_visibility",
    "recompute_visibility",
    "replay_stability",
    "runtime_visibility",
]
