"""Tests for the v2.1 DeficitCategory enum (Aufgabe 2)."""
from __future__ import annotations

from desi.diagnostic import DeficitCategory


_EXPECTED_VALUES = {
    "parser_coverage",
    "logical_rule_coverage",
    "bridge_generation",
    "counterexample_coverage",
    "recursion_configuration",
    "tool_coverage",
    "tool_dependency",
    "benchmark_blind_spot",
    "dead_mutation_knob",
    "false_block_reason",
    "unknown",
}


def test_eleven_values_exactly() -> None:
    assert len(list(DeficitCategory)) == 11


def test_closed_set_matches_directive() -> None:
    assert {c.value for c in DeficitCategory} == _EXPECTED_VALUES


def test_each_directive_name_present() -> None:
    """The directive listed these names verbatim — they must exist."""
    for name in (
        "PARSER_COVERAGE", "LOGICAL_RULE_COVERAGE", "BRIDGE_GENERATION",
        "COUNTEREXAMPLE_COVERAGE", "RECURSION_CONFIGURATION",
        "TOOL_COVERAGE", "TOOL_DEPENDENCY", "BENCHMARK_BLIND_SPOT",
        "DEAD_MUTATION_KNOB", "FALSE_BLOCK_REASON", "UNKNOWN",
    ):
        assert hasattr(DeficitCategory, name), name


def test_enum_is_string_compatible() -> None:
    """The class inherits ``str`` so canonical JSON can serialise it."""
    assert isinstance(DeficitCategory.UNKNOWN.value, str)
