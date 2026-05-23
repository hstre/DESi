"""v1.9 regression contracts (Aufgabe 9): existing 50-case benchmark
metrics MUST remain unchanged after the tool layer is added."""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    cases_by_category,
    compute_metrics,
)
from desi.recursive import BlockingReason, RecursiveResolver, ResolutionState


def test_main_benchmark_precision_remains_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.precision == 1.000


def test_main_benchmark_recall_remains_one() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.recall == 1.000


def test_main_benchmark_false_positives_remain_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.false_positives == 0


def test_authority_remains_ten_of_ten_authority_claim() -> None:
    """v1.8's strengthened authority handling must not regress."""
    for c in cases_by_category(Category.C_AUTHORITY_TRAPS):
        r = RecursiveResolver().resolve(c.text)
        assert r.final_state is ResolutionState.RESOLUTION_BLOCKED, c.case_id
        assert r.blocking_reason is BlockingReason.AUTHORITY_CLAIM, c.case_id


def test_main_benchmark_unjustified_acceptance_remains_zero() -> None:
    m = compute_metrics(BenchmarkRunner().run())
    assert m.unjustified_acceptance_rate == 0.0


def test_no_main_case_dispatches_a_tool() -> None:
    """v1.9 audit (documented in v1_9.md): 0/50 of the existing
    benchmark cases trigger the tool detector. The tool layer is
    purely additive; the existing benchmark is untouched."""
    from desi.benchmark import ALL_CASES
    from desi.tools import ToolDetector
    detector = ToolDetector()
    dispatched = [c.case_id for c in ALL_CASES
                   if detector.detect(c.text) is not None]
    assert dispatched == [], (
        f"tool detector unexpectedly fired on main-benchmark cases: "
        f"{dispatched}"
    )


def test_main_benchmark_reproducibility_intact() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


def test_claimstate_v19_additions_do_not_remove_existing() -> None:
    """The 4 new ClaimState values are additive — every v1.2/v1.7
    state must still exist."""
    from desi.memory.claim import ClaimState
    values = {s.value for s in ClaimState}
    for v in ("proposed", "revised", "confirmed", "rejected", "merged",
              "split", "under_logical_audit", "gap_detected",
              "bridge_required", "logically_supported",
              "logically_rejected"):
        assert v in values, f"v1.9 dropped existing ClaimState: {v}"
    for v in ("tool_required", "tool_supported",
              "tool_refuted", "tool_failed"):
        assert v in values, f"v1.9 missing new ClaimState: {v}"
