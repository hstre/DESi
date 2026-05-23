"""v2.8 regression — no benchmark drift after the protocol module
is added (Aufgabe 6)."""
from __future__ import annotations

from desi.benchmark import BenchmarkRunner, compute_metrics
from desi.benchmark_multistep import MultiStepBenchmarkRunner
from desi.rule_patch_protocol import compute_benchmark_hashes
from desi.tools import ToolBenchmarkRunner


def test_main_benchmark_precision_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000


def test_main_benchmark_recall_unchanged() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.recall == 1.000


def test_main_benchmark_false_positives_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_tool_benchmark_results_count_twenty() -> None:
    run = ToolBenchmarkRunner().run()
    assert len(run.results) == 20


def test_multistep_total_unchanged() -> None:
    run = MultiStepBenchmarkRunner().run()
    assert len(run.results) == 30


def test_benchmark_hashes_are_stable_across_two_calls() -> None:
    a = compute_benchmark_hashes()
    b = compute_benchmark_hashes()
    assert a == b


def test_benchmark_hashes_include_all_six_dimensions() -> None:
    hashes = compute_benchmark_hashes()
    assert set(hashes.keys()) == {
        "v1_5_main", "v1_9_tool", "v2_3_multistep",
        "v2_4_bridge_audit", "v2_5_rule_audit", "v2_6_causal_probe",
    }


def test_forbidden_packages_do_not_import_rule_patch_protocol() -> None:
    """The protocol is a meta-tool — production must not depend on it."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "desi"
    forbidden = (
        "logic", "consilium", "recursive", "tools",
        "memory", "evolution", "spl_adapter",
        "benchmark", "benchmark_multistep",
        "bridge_audit", "causal_probe", "rule_audit",
        "sandbox", "diagnostic",
    )
    pattern = re.compile(r"rule_patch_protocol")
    for sub in forbidden:
        for p in (root / sub).rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            assert not pattern.search(text), (
                f"{p} mentions rule_patch_protocol — directive violation"
            )
