"""Tests for the v2.0 sandbox benchmark gate (Aufgabe 3)."""
from __future__ import annotations

from desi.sandbox import (
    REQUIRED_AUTHORITY_BLOCKS,
    REQUIRED_PRECISION,
    REQUIRED_RECALL,
    REQUIRED_TOOL_PRECISION,
    SandboxBenchmarkGate,
)


def test_baseline_passes_all_six_criteria() -> None:
    v = SandboxBenchmarkGate().evaluate()
    assert v.passed is True
    assert v.failure_reason == ""


def test_baseline_precision_is_one() -> None:
    v = SandboxBenchmarkGate().evaluate()
    assert v.precision == REQUIRED_PRECISION


def test_baseline_recall_is_one() -> None:
    v = SandboxBenchmarkGate().evaluate()
    assert v.recall == REQUIRED_RECALL


def test_baseline_false_positives_is_zero() -> None:
    v = SandboxBenchmarkGate().evaluate()
    assert v.false_positives == 0


def test_baseline_authority_blocks_is_ten() -> None:
    v = SandboxBenchmarkGate().evaluate()
    assert v.authority_blocks == REQUIRED_AUTHORITY_BLOCKS


def test_baseline_tool_precision_is_one() -> None:
    v = SandboxBenchmarkGate().evaluate()
    assert v.tool_precision == REQUIRED_TOOL_PRECISION


def test_baseline_hash_mismatches_is_zero() -> None:
    v = SandboxBenchmarkGate().evaluate()
    assert v.hash_mismatches == 0


def test_verdict_to_dict_has_all_seven_observables() -> None:
    v = SandboxBenchmarkGate().evaluate()
    d = v.to_dict()
    for k in (
        "passed", "precision", "recall", "false_positives",
        "authority_blocks", "tool_precision", "hash_mismatches",
        "failure_reason",
    ):
        assert k in d


def test_two_evaluations_yield_identical_observables() -> None:
    """Stable-v1.9.0 is deterministic; the gate must agree across runs."""
    a = SandboxBenchmarkGate().evaluate()
    b = SandboxBenchmarkGate().evaluate()
    assert a.precision == b.precision
    assert a.recall == b.recall
    assert a.false_positives == b.false_positives
    assert a.authority_blocks == b.authority_blocks
    assert a.tool_precision == b.tool_precision
    assert a.hash_mismatches == b.hash_mismatches
