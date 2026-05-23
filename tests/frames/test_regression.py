"""v3.4 regression — every prior hash and benchmark unchanged.

Aufgabe 9 — FAIL CLOSED if any previous benchmark drifts.
"""
from __future__ import annotations

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    compute_benchmark_hashes,
    fake_rule_without_guards_candidate,
)
from desi.tools import ToolBenchmarkRunner


def test_v15_metrics_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000
    assert m.recall == 1.000
    assert m.false_positives == 0


def test_v19_tool_count_unchanged() -> None:
    assert len(ToolBenchmarkRunner().run().results) == 20


def test_v23_multistep_count_unchanged() -> None:
    assert len(MultiStepBenchmarkRunner().run().results) == 30


def test_benchmark_hashes_stable_across_two_calls() -> None:
    a = compute_benchmark_hashes()
    b = compute_benchmark_hashes()
    assert a == b


def test_v28_reconstruction_replay_hash_pinned() -> None:
    """Pin to the value documented since v2.8."""
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v28_fail_case_replay_hash_pinned() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"
