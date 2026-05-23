"""v34.1 - search-compression benchmark runner.

Executes the search-compression task through the v33 search adapter
and exposes its measured metrics. The runner only dispatches; the
compression measurement lives entirely in the existing adapter.
"""
from __future__ import annotations

from functools import lru_cache

from desi.benchmark_api import BenchmarkResult
from desi.benchmark_api_search import adapter

from .search_tasks import search_task


@lru_cache(maxsize=1)
def run() -> BenchmarkResult:
    return adapter().run(search_task())


def metrics() -> dict[str, float]:
    return run().metric_map()


def metric(name: str) -> float:
    return metrics().get(name, 0.0)


__all__ = [
    "metric",
    "metrics",
    "run",
]
