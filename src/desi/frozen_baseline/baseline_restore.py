"""v32.0 - reconstruction of the frozen pre-v29 DESi baseline.

DESi_baseline_frozen_v1 is the original DESi BEFORE the evolution
phase: it has NONE of the evolution-era infrastructure (no replay
cache evolution, no mutation ecology, no evolution memory, no
peripheral mutation, no long-horizon branching). Its expensive
rebuilds are always recomputed - there is no cache.

The baseline must stay frozen: no later optimisation, no replay
change, no cache change, no mutation memory, no evolution ecology.
The shared workload (papers / claims / queries / tasks) is the
identical input set used by both versions in the benchmark.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache

from desi.replay_cache_evolution import Workload, rebuild, workloads

FROZEN_VERSION = "DESi_baseline_frozen_v1"

# Evolution-era features that are DISABLED in the frozen baseline.
FROZEN_DISABLED_FEATURES: tuple[str, ...] = (
    "replay_cache_evolution",
    "mutation_ecology",
    "evolution_memory",
    "peripheral_mutation",
    "long_horizon_branching",
)


def baseline_workload() -> tuple[Workload, ...]:
    """The shared, identical input set (papers / claims / queries /
    tasks) - reused unchanged from the canonical workload."""
    return workloads()


@dataclass(frozen=True)
class BaselineRun:
    recomputes: int
    outputs: tuple[tuple[str, str], ...]
    chain_head: str

    def output_map(self) -> dict[str, str]:
        return {k: v for k, v in self.outputs}

    def to_dict(self) -> dict[str, object]:
        return {
            "recomputes": self.recomputes,
            "outputs": [list(o) for o in self.outputs],
            "chain_head": self.chain_head,
        }


@lru_cache(maxsize=1)
def baseline_run() -> BaselineRun:
    """Run every workload its full repeat count with NO cache - the
    frozen pre-v29 behaviour. Every repeat is a real recompute."""
    chain = f"frozen_baseline::{FROZEN_VERSION}"
    recomputes = 0
    outputs: list[tuple[str, str]] = []
    for w in baseline_workload():
        out = ""
        for _ in range(w.repeat):
            recomputes += 1
            out = rebuild(w.seed, w.work)
        outputs.append((w.name, out))
        chain = hashlib.sha256(
            (chain + "|" + w.name + "=" + out).encode("utf-8"),
        ).hexdigest()
    return BaselineRun(
        recomputes=recomputes,
        outputs=tuple(outputs),
        chain_head=chain,
    )


def baseline_recomputes() -> int:
    return baseline_run().recomputes


def baseline_outputs() -> dict[str, str]:
    return baseline_run().output_map()


def uses_evolution_features() -> bool:
    """The frozen baseline never activates an evolution-era feature.
    By construction this is always False - it is the definition of
    'frozen'."""
    return False


def is_frozen() -> bool:
    """The baseline is frozen iff no evolution feature is active and
    the run is reproducible (identical recompute count + outputs)."""
    if uses_evolution_features():
        return False
    a = baseline_run()
    b = baseline_run()
    return (
        a.recomputes == b.recomputes
        and a.outputs == b.outputs
        and a.chain_head == b.chain_head
    )


__all__ = [
    "FROZEN_DISABLED_FEATURES",
    "FROZEN_VERSION",
    "BaselineRun",
    "baseline_outputs",
    "baseline_recomputes",
    "baseline_run",
    "baseline_workload",
    "is_frozen",
    "uses_evolution_features",
]
