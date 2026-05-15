"""v2.6 regression — Aufgabe 9.

The causal-chain probe must not perturb v1.5 main, v1.9 tool, v2.3
multistep, v2.4 bridge audit, or v2.5 rule audit. These tests are
the trip-wire.
"""
from __future__ import annotations

from datetime import datetime, timezone

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.bridge_audit import (
    BridgeEntryAuditRunner,
    build_funnel_report,
)
from desi.rule_audit import RuleCoverageRunner, build_rule_coverage_report
from desi.tools import ToolBenchmarkRunner


# ---------------------------------------------------------------------------
# v1.5 main benchmark
# ---------------------------------------------------------------------------


def test_main_precision_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000


def test_main_recall_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.recall == 1.000


def test_main_false_positives_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_main_replay_bit_identical() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


# ---------------------------------------------------------------------------
# v1.9 tool benchmark
# ---------------------------------------------------------------------------


def test_tool_benchmark_results_count() -> None:
    run = ToolBenchmarkRunner().run()
    assert len(run.results) == 20


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
        assert ra.replay_hash == rb.replay_hash


# ---------------------------------------------------------------------------
# v2.4 bridge funnel
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
# v2.5 rule audit
# ---------------------------------------------------------------------------


def test_rule_audit_replay_stable() -> None:
    now = datetime.now(timezone.utc)
    a = build_rule_coverage_report(
        RuleCoverageRunner().run(),
        started_at=now, finished_at=now,
    )
    b = build_rule_coverage_report(
        RuleCoverageRunner().run(),
        started_at=now, finished_at=now,
    )
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# Directive enforcement: no forbidden package imports causal_probe
# ---------------------------------------------------------------------------


def test_forbidden_packages_do_not_import_causal_probe() -> None:
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "desi"
    forbidden = (
        "logic", "consilium", "recursive", "tools",
        "memory", "evolution", "spl_adapter",
        "benchmark", "benchmark_multistep",
    )
    pattern = re.compile(r"causal_probe")
    for sub in forbidden:
        for p in (root / sub).rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions causal_probe — directive violation"
            )
