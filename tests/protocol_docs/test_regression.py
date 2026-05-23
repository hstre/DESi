"""v2.9 regression — verify the documentation patch did not perturb
any benchmark or protocol replay hash (Aufgabe 8)."""
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


def test_v15_precision_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000


def test_v15_recall_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.recall == 1.000


def test_v15_false_positives_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_v19_tool_results_count() -> None:
    run = ToolBenchmarkRunner().run()
    assert len(run.results) == 20


def test_v23_multistep_total_unchanged() -> None:
    run = MultiStepBenchmarkRunner().run()
    assert len(run.results) == 30


def test_compute_benchmark_hashes_stable_across_two_calls() -> None:
    a = compute_benchmark_hashes()
    b = compute_benchmark_hashes()
    assert a == b


def test_v28_reconstruction_replay_hash_stable() -> None:
    proto = RulePatchProtocol()
    a = proto.run(causal_chain_v2_7_candidate())
    b = proto.run(causal_chain_v2_7_candidate())
    assert a.replay_hash == b.replay_hash
    # Pin against the value captured in v2.8.
    assert a.replay_hash == "1f4d9dfe44cb16e1"


def test_v28_fail_case_replay_hash_stable() -> None:
    proto = RulePatchProtocol()
    a = proto.run(fake_rule_without_guards_candidate())
    b = proto.run(fake_rule_without_guards_candidate())
    assert a.replay_hash == b.replay_hash
    assert a.replay_hash == "d83d81ab8417c022"
