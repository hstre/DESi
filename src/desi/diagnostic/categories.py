"""Closed enumeration of deficit categories (Aufgabe 2).

The v2.1 diagnostic discipline forbids ad-hoc deficit kinds. Every
finding must land in exactly one of the eleven values below.
Adding values requires a new directive — silent additions are a
directive violation.
"""
from __future__ import annotations

from enum import Enum


class DeficitCategory(str, Enum):
    PARSER_COVERAGE = "parser_coverage"
    LOGICAL_RULE_COVERAGE = "logical_rule_coverage"
    BRIDGE_GENERATION = "bridge_generation"
    COUNTEREXAMPLE_COVERAGE = "counterexample_coverage"
    RECURSION_CONFIGURATION = "recursion_configuration"
    TOOL_COVERAGE = "tool_coverage"
    TOOL_DEPENDENCY = "tool_dependency"
    BENCHMARK_BLIND_SPOT = "benchmark_blind_spot"
    DEAD_MUTATION_KNOB = "dead_mutation_knob"
    FALSE_BLOCK_REASON = "false_block_reason"
    UNKNOWN = "unknown"


__all__ = ["DeficitCategory"]
