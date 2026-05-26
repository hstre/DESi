"""DESi benchmark ports (PERIPHERAL).

The semantic-flow constitution is immutable. Benchmark layers are peripheral.
Benchmarks run ON DESi. Benchmarks do not redefine DESi.

A thin, optional facade over the tested ``desi.benchmark_api`` boundary that
exposes the standardized benchmark ports — input/output ports, an optional
pluggable extractor interface, an optional runner, and an optional read-only
comparison layer. It introduces no ontology, no governance, and no core logic;
claims appear only as projections.
"""
from __future__ import annotations

from .ports import (
    FORBIDDEN_BENCHMARK_OPERATIONS,
    BenchmarkRunner,
    ExtractorPort,
    compare_results,
    input_port,
    is_forbidden,
    output_port,
    requested_forbidden,
)

__all__ = [
    "FORBIDDEN_BENCHMARK_OPERATIONS",
    "BenchmarkRunner",
    "ExtractorPort",
    "compare_results",
    "input_port",
    "is_forbidden",
    "output_port",
    "requested_forbidden",
]
