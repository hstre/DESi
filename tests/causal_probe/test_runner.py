"""Tests for v2.6 CausalChainProbeRunner (Aufgaben 3, 5)."""
from __future__ import annotations

from desi.causal_probe import (
    BenchmarkSource,
    CausalChainCandidate,
    CausalChainProbeRunner,
    KNOWN_FALSE_POSITIVE_CASE_IDS,
    RiskFlag,
)


def test_runner_covers_eighty_cases() -> None:
    """50 main + 30 multistep = 80 candidates."""
    run = CausalChainProbeRunner().run()
    assert len(run.candidates) == 80


def test_runner_partitions_by_benchmark_source() -> None:
    run = CausalChainProbeRunner().run()
    main = [c for c in run.candidates
            if c.benchmark_source is BenchmarkSource.MAIN_50]
    multi = [c for c in run.candidates
             if c.benchmark_source is BenchmarkSource.MULTISTEP_30]
    assert len(main) == 50
    assert len(multi) == 30


def test_every_candidate_is_a_dataclass() -> None:
    run = CausalChainProbeRunner().run()
    for c in run.candidates:
        assert isinstance(c, CausalChainCandidate)


def test_every_known_false_positive_is_probed() -> None:
    """Aufgabe 8: known FP list must be present in the candidates."""
    run = CausalChainProbeRunner().run()
    seen = {c.case_id for c in run.candidates}
    for fp in KNOWN_FALSE_POSITIVE_CASE_IDS:
        assert fp in seen, f"missing known-FP probe for {fp}"


def test_two_runs_produce_identical_replay_hashes() -> None:
    a = CausalChainProbeRunner().run()
    b = CausalChainProbeRunner().run()
    for ca, cb in zip(a.candidates, b.candidates):
        assert ca.replay_hash == cb.replay_hash, ca.case_id


def test_two_runs_produce_identical_trigger_decisions() -> None:
    a = CausalChainProbeRunner().run()
    b = CausalChainProbeRunner().run()
    for ca, cb in zip(a.candidates, b.candidates):
        assert ca.candidate_triggered == cb.candidate_triggered


def test_every_risk_flag_is_in_closed_enum() -> None:
    run = CausalChainProbeRunner().run()
    closed = set(RiskFlag)
    for c in run.candidates:
        for f in c.risk_flags:
            assert f in closed


def test_non_triggered_candidates_have_no_risk_flags() -> None:
    """Risk flags are only attached to triggered candidates."""
    run = CausalChainProbeRunner().run()
    for c in run.candidates:
        if not c.candidate_triggered:
            assert c.risk_flags == ()


def test_to_dict_round_trip_shape() -> None:
    run = CausalChainProbeRunner().run()
    d = run.candidates[0].to_dict()
    for k in (
        "case_id", "benchmark_source", "text", "premise_count",
        "therefore_count", "atomic_sequence", "repeated_subjects",
        "repeated_predicates", "candidate_triggered", "trigger_reason",
        "risk_flags", "expected_label", "current_final_state",
        "replay_hash",
    ):
        assert k in d


def test_main_case_counts_remain_fifty() -> None:
    """Aufgabe 8: case counts must not drift."""
    run = CausalChainProbeRunner().run()
    main = [c for c in run.candidates
            if c.benchmark_source is BenchmarkSource.MAIN_50]
    assert len(main) == 50


def test_multistep_case_counts_remain_thirty() -> None:
    run = CausalChainProbeRunner().run()
    multi = [c for c in run.candidates
             if c.benchmark_source is BenchmarkSource.MULTISTEP_30]
    assert len(multi) == 30
