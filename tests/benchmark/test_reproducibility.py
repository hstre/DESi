"""Tests for benchmark reproducibility — two runs are bit-identical."""
from __future__ import annotations

from desi.benchmark import (
    BenchmarkRunner,
    compute_metrics,
    render_markdown_report,
)


def test_two_runs_produce_identical_per_case_hashes() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    pairs = list(zip(a.results, b.results))
    for ra, rb in pairs:
        assert ra.case.case_id == rb.case.case_id
        assert ra.replay_hash == rb.replay_hash, ra.case.case_id


def test_two_runs_produce_identical_final_states() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    for ra, rb in zip(a.results, b.results):
        assert ra.final_state == rb.final_state, ra.case.case_id


def test_all_replay_hashes_are_unique_per_case() -> None:
    """No two cases collide on replay_hash. Cases are distinct
    enough that the recursive resolver hashes them apart."""
    run = BenchmarkRunner().run()
    hashes = [r.replay_hash for r in run.results]
    assert len(set(hashes)) == len(hashes)


def test_two_runs_produce_identical_metrics() -> None:
    m1 = compute_metrics(BenchmarkRunner().run())
    m2 = compute_metrics(BenchmarkRunner().run())
    assert m1.total == m2.total
    assert m1.true_positives == m2.true_positives
    assert m1.false_positives == m2.false_positives
    assert m1.false_negatives == m2.false_negatives
    assert m1.precision == m2.precision
    assert m1.recall == m2.recall
    assert m1.overblocking_rate == m2.overblocking_rate
    assert m1.unjustified_acceptance_rate == m2.unjustified_acceptance_rate


def test_report_excluding_timestamp_is_byte_identical_across_runs() -> None:
    a = BenchmarkRunner().run()
    b = BenchmarkRunner().run()
    raw_a = render_markdown_report(a)
    raw_b = render_markdown_report(b)
    # The header line carries the run timestamp; drop it for the
    # byte-identity check.
    def _strip_timestamp(md: str) -> str:
        return "\n".join(
            line for line in md.splitlines()
            if not line.startswith("Run timestamp:")
        )
    assert _strip_timestamp(raw_a) == _strip_timestamp(raw_b)
