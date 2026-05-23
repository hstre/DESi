"""v34.2 - reproducibility task definition.

The reproducibility run executes the same benchmark workload several
times and checks that every observable - outputs, metrics, citations,
artifacts and replay hashes - is byte-identical across runs. The
workload is the v33 harness suite (drift + search) plus the citation
and section surfaces of the output ports.
"""
from __future__ import annotations

REPEATS = 5

REPRO_DIMENSIONS: tuple[str, ...] = (
    "output_identity",
    "metric_identity",
    "citation_identity",
    "artifact_identity",
    "section_identity",
    "replay_hash_identity",
)


def repeats() -> int:
    return REPEATS


__all__ = [
    "REPEATS",
    "REPRO_DIMENSIONS",
    "repeats",
]
