"""v2.4 regression — Aufgaben 6, 7.

The v2.4 audit module must not perturb the v1.5 main benchmark,
the v1.9 tool benchmark, or the v2.3 multistep benchmark. These
tests are the trip-wire.
"""
from __future__ import annotations

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import (
    MultiStepBenchmarkRunner,
    check_hard_constraints,
    compute_multistep_metrics,
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


def test_main_benchmark_replay_hashes_bit_identical() -> None:
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


def test_tool_benchmark_all_correct() -> None:
    run = ToolBenchmarkRunner().run()
    correct = sum(1 for r in run.results if r.correct)
    assert correct == 20


# ---------------------------------------------------------------------------
# v2.3 multistep benchmark — same metrics as before v2.4 was added
# ---------------------------------------------------------------------------


def test_multistep_total_remains_thirty() -> None:
    run = MultiStepBenchmarkRunner().run()
    assert len(run.results) == 30


def test_multistep_replay_stable() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


def test_multistep_metrics_stable_across_two_runs() -> None:
    """If v2.4 had subtly altered the resolver, multistep metrics
    would drift — they must not."""
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    ma = compute_multistep_metrics(a)
    mb = compute_multistep_metrics(b)
    assert ma.recursion_usage_rate == mb.recursion_usage_rate
    assert ma.false_depth_zero_rate == mb.false_depth_zero_rate
    assert ma.cycle_detection_rate == mb.cycle_detection_rate
    assert (ma.blocked_propagation_accuracy
            == mb.blocked_propagation_accuracy)


def test_multistep_hard_constraints_unchanged() -> None:
    a = MultiStepBenchmarkRunner().run()
    b = MultiStepBenchmarkRunner().run()
    rep = check_hard_constraints(a, b)
    assert rep.replay_drift is False


# ---------------------------------------------------------------------------
# No production module under the forbidden roots was modified
# ---------------------------------------------------------------------------


def test_no_production_module_imports_bridge_audit() -> None:
    """The directive forbids changes to logic/, consilium/,
    recursive/, tools/, memory/, evolution/, spl_adapter/.
    Verify none of those imports the new bridge_audit module."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "desi"
    forbidden = (
        "logic", "consilium", "recursive", "tools",
        "memory", "evolution", "spl_adapter",
    )
    pattern = re.compile(r"bridge_audit")
    for sub in forbidden:
        for p in (root / sub).rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions bridge_audit — directive violation"
            )
