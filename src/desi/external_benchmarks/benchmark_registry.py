"""v35.0 - benchmark family registry.

Maps each supported benchmark family to the dataset that backs it and
to the v33 adapter route it normalises into. This is the single
source of truth for which external families DESi can ingest.
"""
from __future__ import annotations

from .dataset_loader import Dataset, load_dataset

# family -> (dataset name, internal route)
ROUTE_DRIFT = "drift"
ROUTE_SEARCH = "search"
ROUTE_REPRODUCIBILITY = "reproducibility"
ROUTE_RENDERING = "rendering"

_REGISTRY: dict[str, tuple[str, str]] = {
    "BeliefShift": ("beliefshift_ref", ROUTE_DRIFT),
    "MemEvoBench": ("memevo_ref", ROUTE_DRIFT),
    "AgentDrift": ("agentdrift_ref", ROUTE_DRIFT),
    "ToolChain": ("toolchain_ref", ROUTE_SEARCH),
}

# Families served by existing in-repo pipelines rather than a new
# external dataset file (reproducibility & citation reuse v34).
_PIPELINE_FAMILIES: dict[str, str] = {
    "Reproducibility": ROUTE_REPRODUCIBILITY,
    "ScientificRendering": ROUTE_RENDERING,
}

BENCHMARK_FAMILIES: tuple[str, ...] = tuple(_REGISTRY) + tuple(
    _PIPELINE_FAMILIES
)


def dataset_families() -> tuple[str, ...]:
    return tuple(_REGISTRY)


def dataset_name_for(family: str) -> str:
    return _REGISTRY[family][0]


def route_for(family: str) -> str:
    if family in _REGISTRY:
        return _REGISTRY[family][1]
    return _PIPELINE_FAMILIES[family]


def dataset_for(family: str) -> Dataset:
    return load_dataset(dataset_name_for(family))


def families_for_route(route: str) -> tuple[str, ...]:
    out = [f for f, (_, r) in _REGISTRY.items() if r == route]
    out += [f for f, r in _PIPELINE_FAMILIES.items() if r == route]
    return tuple(out)


__all__ = [
    "BENCHMARK_FAMILIES",
    "ROUTE_DRIFT",
    "ROUTE_RENDERING",
    "ROUTE_REPRODUCIBILITY",
    "ROUTE_SEARCH",
    "dataset_families",
    "dataset_for",
    "dataset_name_for",
    "families_for_route",
    "route_for",
]
