"""v29.0 - baseline rebuild workloads (uncached).

Defines representative deterministic rebuild workloads that model
DESi's recompute paths (graph signature, render section, ecology
chain, results assembly). Each rebuild does real CPU work (a
deterministic sha256 chain) and is fully reproducible. The
baseline executes every workload its full repeat count with no
cache - the recompute explosion that the v29.1 branch removes.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .timing import RecomputeCounter

# (name, seed, work_iterations, repeat_count). repeat > 1 means
# the same artifact is rebuilt repeatedly across call sites - a
# cache opportunity.
_WORKLOADS: tuple[tuple[str, str, int, int], ...] = (
    ("graph_signature_rebuild", "graph", 20000, 12),
    ("render_section_rebuild", "render", 15000, 10),
    ("ecology_chain_rebuild", "ecology", 25000, 8),
    ("results_assembly_rebuild", "results", 12000, 6),
)


@dataclass(frozen=True)
class Workload:
    name: str
    seed: str
    work: int
    repeat: int

    def is_cacheable(self) -> bool:
        return self.repeat > 1

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "seed": self.seed,
            "work": self.work,
            "repeat": self.repeat,
            "is_cacheable": self.is_cacheable(),
        }


def workloads() -> tuple[Workload, ...]:
    return tuple(
        Workload(n, s, w, r) for n, s, w, r in _WORKLOADS
    )


def rebuild(seed: str, work: int) -> str:
    """A real, deterministic, uncached rebuild (sha256 chain)."""
    h = f"rebuild::{seed}"
    for i in range(work):
        h = hashlib.sha256(
            (h + str(i)).encode("utf-8"),
        ).hexdigest()
    return h


def workload_output_hash(w: Workload) -> str:
    return rebuild(w.seed, w.work)


def baseline_run() -> tuple[RecomputeCounter, dict[str, str]]:
    """Execute every workload its full repeat count with no
    cache. Returns the recompute counter (all misses) and the
    per-workload output hash."""
    counter = RecomputeCounter()
    outputs: dict[str, str] = {}
    for w in workloads():
        out = ""
        for _ in range(w.repeat):
            counter.record_miss()
            out = rebuild(w.seed, w.work)
        outputs[w.name] = out
    return counter, outputs


def baseline_recompute_count() -> int:
    """Total rebuilds the baseline performs (sum of repeats)."""
    return sum(w.repeat for w in workloads())


def output_hashes() -> dict[str, str]:
    return {w.name: workload_output_hash(w) for w in workloads()}


__all__ = [
    "Workload",
    "baseline_recompute_count",
    "baseline_run",
    "output_hashes",
    "rebuild",
    "workload_output_hash",
    "workloads",
]
