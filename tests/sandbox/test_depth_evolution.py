"""End-to-end tests for v2.2 DepthEvolutionSandbox (Aufgaben 1, 9)."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from desi.sandbox import (
    DEPTH_MAX,
    DEPTH_MIN,
    DepthEvolutionReport,
    DepthEvolutionSandbox,
    DepthLedgerEventType,
    DepthStepOutcome,
    DepthStressSuite,
    GateVerdict,
)


# A clean gate so unit tests don't pay for the full benchmark
# 30 times.
@dataclass
class _CleanGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=True, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
        )


@dataclass
class _DirtyGate:
    """A gate that returns a precision regression."""

    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=False, precision=0.96, recall=1.0, false_positives=2,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
            failure_reason="false_positives=2",
        )


# ---------------------------------------------------------------------------
# Aufgabe 1 — basic run + stable invariant
# ---------------------------------------------------------------------------


def test_run_returns_depth_evolution_report() -> None:
    sb = DepthEvolutionSandbox(n_steps=3, gate=_CleanGate())
    rep = sb.run()
    assert isinstance(rep, DepthEvolutionReport)


def test_thirty_step_default_completes() -> None:
    sb = DepthEvolutionSandbox(
        start_depth=3, n_steps=30, gate=_CleanGate(),
    )
    rep = sb.run()
    assert rep.total_steps == 30


def test_stable_hash_unchanged_after_run() -> None:
    sb = DepthEvolutionSandbox(n_steps=5, gate=_CleanGate())
    rep = sb.run()
    assert rep.stable_hash_before == rep.stable_hash_after


def test_invalid_start_depth_rejected() -> None:
    with pytest.raises(ValueError):
        DepthEvolutionSandbox(start_depth=0, gate=_CleanGate())
    with pytest.raises(ValueError):
        DepthEvolutionSandbox(start_depth=7, gate=_CleanGate())


def test_invalid_n_steps_rejected() -> None:
    with pytest.raises(ValueError):
        DepthEvolutionSandbox(n_steps=0, gate=_CleanGate())


# ---------------------------------------------------------------------------
# Aufgabe 9 — report fields + determinism
# ---------------------------------------------------------------------------


def test_report_carries_all_required_fields() -> None:
    sb = DepthEvolutionSandbox(n_steps=3, gate=_CleanGate())
    rep = sb.run()
    for attr in (
        "total_steps", "accepted_steps", "rejected_steps",
        "best_depth", "starting_depth", "depth_history",
        "plateau_detected", "oscillation_detected",
        "convergence_detected", "best_fitness",
        "recommended_depth", "replay_hash",
    ):
        assert hasattr(rep, attr), attr


def test_two_runs_produce_identical_replay_hash() -> None:
    a = DepthEvolutionSandbox(start_depth=3, n_steps=5,
                              gate=_CleanGate()).run()
    b = DepthEvolutionSandbox(start_depth=3, n_steps=5,
                              gate=_CleanGate()).run()
    assert a.replay_hash == b.replay_hash


def test_recommended_depth_in_legal_range() -> None:
    sb = DepthEvolutionSandbox(n_steps=5, gate=_CleanGate())
    rep = sb.run()
    assert DEPTH_MIN <= rep.recommended_depth <= DEPTH_MAX


def test_depth_history_length_is_steps_plus_one() -> None:
    sb = DepthEvolutionSandbox(n_steps=5, gate=_CleanGate())
    rep = sb.run()
    assert len(rep.depth_history) == 6   # starting + 5 steps


def test_depth_history_starts_at_start_depth() -> None:
    sb = DepthEvolutionSandbox(
        start_depth=4, n_steps=2, gate=_CleanGate(),
    )
    rep = sb.run()
    assert rep.depth_history[0] == 4


def test_step_changes_are_at_most_one() -> None:
    """Hard invariant of Aufgabe 2."""
    sb = DepthEvolutionSandbox(n_steps=20, gate=_CleanGate())
    rep = sb.run()
    for a, b in zip(rep.depth_history, rep.depth_history[1:]):
        assert abs(b - a) <= 1


# ---------------------------------------------------------------------------
# Aufgabe 4 — fitness kill paths
# ---------------------------------------------------------------------------


def test_dirty_gate_rejects_every_step() -> None:
    """A gate that reports FPs triggers the kill condition in the
    fitness function -- step is rejected, not crashed."""
    sb = DepthEvolutionSandbox(n_steps=3, gate=_DirtyGate())
    rep = sb.run()
    assert rep.rejected_steps == 3
    assert rep.accepted_steps == 0
    for s in rep.steps:
        assert s.fitness_killed is True
        assert s.failure_reason


def test_starting_depth_recorded() -> None:
    sb = DepthEvolutionSandbox(start_depth=5, n_steps=2,
                                gate=_CleanGate())
    rep = sb.run()
    assert rep.starting_depth == 5


# ---------------------------------------------------------------------------
# Aufgabe 7 — ledger discipline
# ---------------------------------------------------------------------------


def test_each_step_emits_five_ledger_events() -> None:
    """PROPOSED + APPLIED + STRESS_STARTED + STRESS_COMPLETED +
    ACCEPTED/REJECTED == 5 events per step."""
    n = 3
    sb = DepthEvolutionSandbox(n_steps=n, gate=_CleanGate())
    sb.run()
    proposed = sb.ledger.filter(DepthLedgerEventType.DEPTH_MUTATION_PROPOSED)
    applied = sb.ledger.filter(DepthLedgerEventType.DEPTH_MUTATION_APPLIED)
    ss_start = sb.ledger.filter(DepthLedgerEventType.DEPTH_STRESS_STARTED)
    ss_end = sb.ledger.filter(DepthLedgerEventType.DEPTH_STRESS_COMPLETED)
    assert len(proposed) == n
    assert len(applied) == n
    assert len(ss_start) == n
    assert len(ss_end) == n


def test_total_ledger_events_match_step_count() -> None:
    n = 4
    sb = DepthEvolutionSandbox(n_steps=n, gate=_CleanGate())
    sb.run()
    # 5 events per step
    assert len(sb.ledger) == n * 5


# ---------------------------------------------------------------------------
# Success criteria from the directive
# ---------------------------------------------------------------------------


def test_recommended_depth_is_in_range_one_to_six_when_clean() -> None:
    sb = DepthEvolutionSandbox(start_depth=3, n_steps=30,
                                gate=_CleanGate())
    rep = sb.run()
    assert 1 <= rep.recommended_depth <= 6
