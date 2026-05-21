"""v35.2 - ToolChain search runner over real connector data.

Loads the connector-vendored ToolChain dataset's branches and assigns
each a compression mode using the v33 search discipline: critical
branches are KEPT (never hard-pruned), redundant branches are reused
or merged (lossless), and the remaining non-critical branches are
soft-reweighted (reversible). A SEARCH_COMPRESSION task bound to the
dataset hash is also run through the v33 search adapter to obtain a
governance-tagged, replay-bound result envelope.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.benchmark_api import (
    SEARCH_COMPRESSION_BENCHMARK, BenchmarkResult, make_task,
)
from desi.benchmark_api_search import (
    MODE_KEPT, MODE_REDUNDANT_COMPRESSION, MODE_REPLAY_REUSE,
    MODE_SOFT_REWEIGHTING, adapter,
)
from desi.external_benchmarks import dataset_for

_LOSSLESS = frozenset({
    MODE_KEPT, MODE_SOFT_REWEIGHTING, MODE_REPLAY_REUSE,
    MODE_REDUNDANT_COMPRESSION,
})


@dataclass(frozen=True)
class RealBranch:
    branch_id: str
    critical: bool
    redundant: bool
    novelty: float
    quality: float
    mode: str

    @property
    def visible(self) -> bool:
        return self.mode in _LOSSLESS

    @property
    def recomputed(self) -> bool:
        return self.mode in (MODE_KEPT, MODE_SOFT_REWEIGHTING)


def _assign_mode(item: dict, redundant_index: int) -> str:
    if item.get("critical"):
        return MODE_KEPT
    if item.get("redundant"):
        # alternate redundant handling between reuse and merge
        return (
            MODE_REPLAY_REUSE if redundant_index % 2 == 0
            else MODE_REDUNDANT_COMPRESSION
        )
    return MODE_SOFT_REWEIGHTING


@lru_cache(maxsize=1)
def real_branches() -> tuple[RealBranch, ...]:
    ds = dataset_for("ToolChain")
    out: list[RealBranch] = []
    redundant_index = 0
    for item in ds.items():
        is_redundant = bool(item.get("redundant"))
        mode = _assign_mode(item, redundant_index)
        if is_redundant:
            redundant_index += 1
        out.append(RealBranch(
            branch_id=str(item["branch_id"]),
            critical=bool(item.get("critical")),
            redundant=is_redundant,
            novelty=float(item.get("novelty", 0.0)),
            quality=float(item.get("quality", 0.0)),
            mode=mode,
        ))
    return tuple(out)


def dataset_hash() -> str:
    return dataset_for("ToolChain").content_hash


@lru_cache(maxsize=1)
def adapter_envelope() -> BenchmarkResult:
    """Run a SEARCH_COMPRESSION task bound to the ToolChain dataset
    hash through the v33 search adapter for a replay-bound,
    governance-tagged envelope."""
    task = make_task(
        task_id="real_search::toolchain",
        benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
        payload={
            "dataset_hash": dataset_hash(),
            "provenance": dataset_for("ToolChain").provenance,
            "branches": len(real_branches()),
        },
        allowed_operations=(
            "adapter", "traceable_mapping", "map_to_internal_metric",
            "scorecard",
        ),
    )
    return adapter().run(task)


def total_branches() -> int:
    return len(real_branches())


__all__ = [
    "RealBranch",
    "adapter_envelope",
    "dataset_hash",
    "real_branches",
    "total_branches",
]
