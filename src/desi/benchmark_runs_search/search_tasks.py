"""v34.1 - concrete search-compression benchmark tasks.

Builds the search-compression benchmark task and names the aspects
the run measures. The task is routed through the v33 search adapter;
the aspects (redundant / low-information / critical / novelty
branches, soft-reweighting vs hard-pruning, replay reuse) are read
off the adapter's measured branch metrics. No new adapter is built.
"""
from __future__ import annotations

from desi.benchmark_api import (
    SEARCH_COMPRESSION_BENCHMARK, BenchmarkTask, make_task,
)
from desi.benchmark_api_search import total_nodes

SEARCH_RUN_ASPECTS: tuple[str, ...] = (
    "redundant_branches",
    "low_information_branches",
    "critical_branches",
    "novelty_branches",
    "soft_vs_hard",
    "replay_reuse",
)


def search_task() -> BenchmarkTask:
    return make_task(
        task_id="search_run::compression",
        benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
        payload={"branches": total_nodes(), "budget": 25,
                 "aspects": len(SEARCH_RUN_ASPECTS)},
        allowed_operations=(
            "adapter", "traceable_mapping", "map_to_internal_metric",
            "scorecard",
        ),
    )


__all__ = [
    "SEARCH_RUN_ASPECTS",
    "search_task",
]
