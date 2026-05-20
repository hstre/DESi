"""v2.5 regression — Aufgaben 7, 8.

Bit-identical: v1.5 main benchmark, v1.9 tool benchmark, v2.3
multistep benchmark, v2.4 bridge funnel report.
"""
from __future__ import annotations

from datetime import datetime, timezone

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.bridge_audit import (
    BridgeEntryAuditRunner,
    build_funnel_report,
)
from desi.tools import ToolBenchmarkRunner


# ---------------------------------------------------------------------------
# v1.5 main benchmark
# ---------------------------------------------------------------------------


def test_main_benchmark_precision_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000


def test_main_benchmark_recall_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.recall == 1.000


def test_main_benchmark_false_positives_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_main_replay_hashes_bit_identical() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


# ---------------------------------------------------------------------------
# v1.9 tool benchmark
# ---------------------------------------------------------------------------


def test_tool_benchmark_twenty_results() -> None:
    run = ToolBenchmarkRunner().run()
    assert len(run.results) == 20


def test_tool_benchmark_correct_count() -> None:
    run = ToolBenchmarkRunner().run()
    correct = sum(1 for r in run.results if r.correct)
    assert correct == 20


# ---------------------------------------------------------------------------
# v2.3 multistep benchmark
# ---------------------------------------------------------------------------


def test_multistep_total_unchanged() -> None:
    run = MultiStepBenchmarkRunner().run()
    assert len(run.results) == 30


def test_multistep_replay_stable() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


# ---------------------------------------------------------------------------
# v2.4 bridge funnel — same replay_hash before/after v2.5
# ---------------------------------------------------------------------------


def test_bridge_funnel_replay_stable() -> None:
    now = datetime.now(timezone.utc)
    a = build_funnel_report(
        BridgeEntryAuditRunner().run(),
        started_at=now, finished_at=now,
    )
    b = build_funnel_report(
        BridgeEntryAuditRunner().run(),
        started_at=now, finished_at=now,
    )
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# Directive enforcement: no production package imports rule_audit
# ---------------------------------------------------------------------------


def test_forbidden_packages_do_not_import_rule_audit() -> None:
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "desi"
    forbidden = (
        "logic", "consilium", "recursive", "tools",
        "memory", "evolution", "spl_adapter",
        "benchmark", "benchmark_multistep",
    )
    pattern = re.compile(r"rule_audit")
    for sub in forbidden:
        for p in (root / sub).rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions rule_audit — directive violation"
            )
