"""v32.1 - real comparative benchmark: baseline vs mutated.

A real, measured comparison of DESi_baseline_frozen_v1 (no cache,
every rebuild recomputed) against DESi_mutated_v31 (replay-safe
memoisation, each distinct rebuild computed once) over the IDENTICAL
shared workload. The mutated version produces byte-identical outputs
while performing far fewer recomputes. The gated, stored metric is
the deterministic recompute reduction; wall-clock is observed live
but never stored because it is non-deterministic. No projected
metrics, no synthetic estimates.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.frozen_baseline import baseline_run, baseline_workload
from desi.replay_cache_evolution import rebuild

MUTATED_VERSION = "DESi_mutated_v31"


@dataclass(frozen=True)
class MutatedRun:
    recomputes: int
    outputs: tuple[tuple[str, str], ...]

    def output_map(self) -> dict[str, str]:
        return {k: v for k, v in self.outputs}


@lru_cache(maxsize=1)
def mutated_run() -> MutatedRun:
    """The mutated v31 version: replay-safe memoisation over the
    same workload. Each distinct (seed, work) is computed once and
    reused for every repeat."""
    cache: dict[tuple[str, int], str] = {}
    recomputes = 0
    outputs: list[tuple[str, str]] = []
    for w in baseline_workload():
        key = (w.seed, w.work)
        out = ""
        for _ in range(w.repeat):
            if key not in cache:
                recomputes += 1
                cache[key] = rebuild(w.seed, w.work)
            out = cache[key]
        outputs.append((w.name, out))
    return MutatedRun(recomputes=recomputes, outputs=tuple(outputs))


def baseline_recomputes() -> int:
    return baseline_run().recomputes


def mutated_recomputes() -> int:
    return mutated_run().recomputes


def measured_improvement() -> float:
    """Real, deterministic recompute reduction in [0, 1]
    (baseline -> mutated). Measured, not projected."""
    base = baseline_recomputes()
    if base <= 0:
        return 0.0
    return (base - mutated_recomputes()) / base


def outputs_identical() -> bool:
    """The mutated version produces byte-identical outputs."""
    return baseline_run().output_map() == mutated_run().output_map()


__all__ = [
    "MUTATED_VERSION",
    "MutatedRun",
    "baseline_recomputes",
    "measured_improvement",
    "mutated_recomputes",
    "mutated_run",
    "outputs_identical",
]
