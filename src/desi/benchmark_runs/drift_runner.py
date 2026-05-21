"""v34.0 - drift benchmark runner.

Executes every drift run task through the v33 drift adapter and
collects the replay-bound results. The runner adds no logic of its
own beyond dispatch - it exercises the existing adapter, so DESi is
tested, not adapted.
"""
from __future__ import annotations

from desi.benchmark_api import BenchmarkResult
from desi.benchmark_api_drift import adapter

from .drift_tasks import DriftRunTask, drift_run_tasks


def run_one(rt: DriftRunTask) -> BenchmarkResult:
    return adapter().run(rt.task)


def run_all() -> tuple[tuple[DriftRunTask, BenchmarkResult], ...]:
    return tuple((rt, run_one(rt)) for rt in drift_run_tasks())


def result_for(name: str) -> BenchmarkResult:
    for rt, res in run_all():
        if rt.name == name:
            return res
    raise KeyError(name)


def _metric(result: BenchmarkResult, dim: str) -> float:
    return result.metric_map().get(dim, 0.0)


def claim_drift_of(name: str) -> float:
    return _metric(result_for(name), "claim_drift")


def core_drift_total_of(name: str) -> float:
    res = result_for(name)
    return sum(
        _metric(res, dim) for dim in (
            "governance_drift", "lineage_drift", "artifact_drift",
            "authority_drift", "replay_drift",
        )
    )


def is_refused(name: str) -> bool:
    return result_for(name).is_refusal()


__all__ = [
    "claim_drift_of",
    "core_drift_total_of",
    "is_refused",
    "result_for",
    "run_all",
    "run_one",
]
