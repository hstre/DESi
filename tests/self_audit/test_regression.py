"""v3.0 regression — runtime + all upstream protocol hashes stable."""
from __future__ import annotations

from datetime import datetime, timezone

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


def test_v15_fp_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_v19_tool_results_count() -> None:
    assert len(ToolBenchmarkRunner().run().results) == 20


def test_v23_multistep_count() -> None:
    assert len(MultiStepBenchmarkRunner().run().results) == 30


def test_benchmark_hashes_stable() -> None:
    a = compute_benchmark_hashes()
    b = compute_benchmark_hashes()
    assert a == b


def test_v28_reconstruction_replay_hash_pinned() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v28_fail_case_replay_hash_pinned() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"


def test_forbidden_packages_do_not_import_self_audit() -> None:
    """v3.0 is a meta-tool; no runtime module may depend on it."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "desi"
    forbidden = (
        "logic", "consilium", "recursive", "tools",
        "memory", "evolution", "spl_adapter",
        "benchmark", "benchmark_multistep",
        "bridge_audit", "causal_probe", "rule_audit",
        "sandbox", "diagnostic", "rule_patch_protocol",
    )
    pattern = re.compile(r"self_audit")
    for sub in forbidden:
        for p in (root / sub).rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions self_audit — directive violation"
            )
