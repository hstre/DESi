"""v2.3 regression: existing benchmarks must remain bit-identical
(Aufgabe 6).

The directive's stop-on-regression rule: if either the v1.5 main
benchmark or the v1.9 tool benchmark drifts after the v2.3 module
is added, STOP. These tests are the trip-wire.
"""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    cases_by_category,
    compute_metrics,
)
from desi.recursive import BlockingReason, RecursiveResolver, ResolutionState
from desi.tools import ToolBenchmarkRunner


# ---------------------------------------------------------------------------
# v1.5 main benchmark
# ---------------------------------------------------------------------------


def test_main_benchmark_precision_remains_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000


def test_main_benchmark_recall_remains_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.recall == 1.000


def test_main_benchmark_false_positives_remain_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_main_benchmark_unjustified_acceptance_remains_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.unjustified_acceptance_rate == 0.0


def test_main_benchmark_replay_hashes_bit_identical() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


def test_authority_cases_still_block_with_authority_claim() -> None:
    """v1.8 contract — must survive the v2.3 module addition."""
    for c in cases_by_category(Category.C_AUTHORITY_TRAPS):
        from desi.recursive import RecursiveResolver
        r = RecursiveResolver().resolve(c.text)
        assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
        assert r.blocking_reason is BlockingReason.AUTHORITY_CLAIM


# ---------------------------------------------------------------------------
# v1.9 tool benchmark
# ---------------------------------------------------------------------------


def test_tool_benchmark_yields_twenty_results() -> None:
    run = ToolBenchmarkRunner().run()
    assert len(run.results) == 20


def test_tool_benchmark_replay_hashes_stable() -> None:
    a = ToolBenchmarkRunner().run()
    b = ToolBenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        if ra.tool_result is None:
            assert rb.tool_result is None
            continue
        if ra.tool_result.provenance is None:
            assert rb.tool_result.provenance is None
            continue
        assert (ra.tool_result.provenance.input_hash
                == rb.tool_result.provenance.input_hash)
        assert (ra.tool_result.provenance.output_hash
                == rb.tool_result.provenance.output_hash)


def test_tool_benchmark_correct_count_unchanged() -> None:
    """The 20/20 contract from v1.9 must still hold."""
    run = ToolBenchmarkRunner().run()
    correct = sum(1 for r in run.results if r.correct)
    assert correct == 20


# ---------------------------------------------------------------------------
# v2.3 must not have polluted the main / tool benchmarks
# ---------------------------------------------------------------------------


def test_no_main_benchmark_case_uses_multistep_text() -> None:
    """The 30 multi-step texts must NOT appear inside the main
    benchmark's case set — otherwise the regression is masked."""
    from desi.benchmark import ALL_CASES
    from desi.benchmark_multistep import ALL_MULTISTEP_CASES
    main_texts = {c.text for c in ALL_CASES}
    ms_texts = {c.text for c in ALL_MULTISTEP_CASES}
    assert main_texts.isdisjoint(ms_texts), (
        f"v2.3 texts leaked into the v1.5 benchmark"
    )
