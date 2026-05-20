"""End-to-end tests for EvolutionSandbox (Aufgaben 1, 5, 6)."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from desi.sandbox import (
    EvolutionReport,
    EvolutionSandbox,
    GateVerdict,
    ShadowLedgerEventType,
    StepOutcome,
)


# A tiny stub gate is used everywhere except a single end-to-end run
# so unit tests do not pay the ~30 s cost of the full benchmark per
# step.
@dataclass
class _AlwaysPassGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=True, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
        )


@dataclass
class _AlwaysFailGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=False, precision=0.999, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
            failure_reason="precision=0.999 != 1.000",
        )


class _CrashingGate:
    def evaluate(self) -> GateVerdict:
        raise RuntimeError("simulated crash inside benchmark")


# ---------------------------------------------------------------------------
# Aufgabe 1 — basic run shape
# ---------------------------------------------------------------------------


def test_run_returns_evolution_report() -> None:
    sb = EvolutionSandbox(n_steps=3, gate=_AlwaysPassGate())
    rep = sb.run()
    assert isinstance(rep, EvolutionReport)
    assert rep.total_steps == 3
    assert len(rep.steps) == 3


def test_thirty_step_default_runs_to_completion() -> None:
    sb = EvolutionSandbox(n_steps=30, gate=_AlwaysPassGate())
    rep = sb.run()
    assert rep.total_steps == 30
    assert rep.accepted_steps + rep.rejected_steps + rep.killed_steps == 30


def test_stable_fingerprint_unchanged_after_run() -> None:
    """The hardest invariant: stable-v1.9.0 source must not change."""
    sb = EvolutionSandbox(n_steps=5, gate=_AlwaysPassGate())
    rep = sb.run()
    assert rep.stable_hash_before == rep.stable_hash_after


def test_stable_version_recorded() -> None:
    sb = EvolutionSandbox(n_steps=1, gate=_AlwaysPassGate())
    rep = sb.run()
    assert rep.stable_version == "stable-v1.9.0"


# ---------------------------------------------------------------------------
# Aufgabe 2 — single-knob invariant per step
# ---------------------------------------------------------------------------


def test_every_step_records_the_one_mutable_knob() -> None:
    sb = EvolutionSandbox(n_steps=10, gate=_AlwaysPassGate())
    rep = sb.run()
    for s in rep.steps:
        assert s.parameter == "branch_open_evidence_min"


# ---------------------------------------------------------------------------
# Aufgabe 3 — gate failures produce REJECTED, not exceptions
# ---------------------------------------------------------------------------


def test_failing_gate_rejects_every_step() -> None:
    sb = EvolutionSandbox(n_steps=4, gate=_AlwaysFailGate())
    rep = sb.run()
    assert rep.rejected_steps == 4
    assert rep.accepted_steps == 0
    assert rep.killed_steps == 0


def test_failing_gate_does_not_advance_parent_value() -> None:
    sb = EvolutionSandbox(
        n_steps=4, gate=_AlwaysFailGate(), initial_value=0.45,
    )
    rep = sb.run()
    # Final value never moves because no step was accepted.
    assert rep.final_parameter_value == 0.45


# ---------------------------------------------------------------------------
# Aufgabe 4 — every step lands in the shadow ledger
# ---------------------------------------------------------------------------


def test_ledger_records_sandbox_started_and_completed_exactly_once() -> None:
    sb = EvolutionSandbox(n_steps=2, gate=_AlwaysPassGate())
    sb.run()
    started = sb.ledger.filter(ShadowLedgerEventType.SANDBOX_STARTED)
    completed = sb.ledger.filter(ShadowLedgerEventType.SANDBOX_COMPLETED)
    assert len(started) == 1
    assert len(completed) == 1


def test_each_step_emits_five_ledger_events() -> None:
    """A clean (passing) step emits: PROPOSED, APPLIED, BENCH_STARTED,
    BENCH_COMPLETED, MUTATION_ACCEPTED. Five per step."""
    n = 3
    sb = EvolutionSandbox(n_steps=n, gate=_AlwaysPassGate())
    sb.run()
    proposed = sb.ledger.filter(ShadowLedgerEventType.MUTATION_PROPOSED)
    applied = sb.ledger.filter(ShadowLedgerEventType.MUTATION_APPLIED)
    bs = sb.ledger.filter(ShadowLedgerEventType.BENCHMARK_STARTED)
    bc = sb.ledger.filter(ShadowLedgerEventType.BENCHMARK_COMPLETED)
    acc = sb.ledger.filter(ShadowLedgerEventType.MUTATION_ACCEPTED)
    assert len(proposed) == n
    assert len(applied) == n
    assert len(bs) == n
    assert len(bc) == n
    assert len(acc) == n


# ---------------------------------------------------------------------------
# Aufgabe 5 — kill switch
# ---------------------------------------------------------------------------


def test_unexpected_exception_in_gate_does_not_crash_sandbox() -> None:
    sb = EvolutionSandbox(n_steps=2, gate=_CrashingGate())
    rep = sb.run()
    assert rep.total_steps == 2
    assert rep.killed_steps == 2


def test_kill_switch_rolls_back_to_prior_parent_value() -> None:
    """After a KILLED step, the next step's parent_value is unchanged."""
    sb = EvolutionSandbox(
        n_steps=3, gate=_CrashingGate(), initial_value=0.45,
    )
    rep = sb.run()
    assert all(s.outcome is StepOutcome.KILLED for s in rep.steps)
    assert rep.final_parameter_value == 0.45


def test_abort_on_kill_stops_immediately() -> None:
    sb = EvolutionSandbox(
        n_steps=10, gate=_CrashingGate(), abort_on_kill=True,
    )
    rep = sb.run()
    assert len(rep.steps) == 1
    assert rep.steps[0].outcome is StepOutcome.KILLED


# ---------------------------------------------------------------------------
# Aufgabe 6 — report fields + deterministic replay_hash
# ---------------------------------------------------------------------------


def test_report_carries_all_required_fields() -> None:
    sb = EvolutionSandbox(n_steps=3, gate=_AlwaysPassGate())
    rep = sb.run()
    for attr in (
        "total_steps", "accepted_steps", "rejected_steps",
        "best_clone_hash", "best_parameter_value",
        "local_optima_detected", "oscillation_detected",
        "convergence_detected", "replay_hash",
    ):
        assert hasattr(rep, attr), attr


def test_replay_hash_is_deterministic_across_runs() -> None:
    a = EvolutionSandbox(n_steps=5, gate=_AlwaysPassGate()).run()
    b = EvolutionSandbox(n_steps=5, gate=_AlwaysPassGate()).run()
    assert a.replay_hash == b.replay_hash


def test_replay_hash_differs_when_step_count_differs() -> None:
    a = EvolutionSandbox(n_steps=3, gate=_AlwaysPassGate()).run()
    b = EvolutionSandbox(n_steps=4, gate=_AlwaysPassGate()).run()
    assert a.replay_hash != b.replay_hash


def test_best_clone_is_an_accepted_step_when_any_accepted() -> None:
    sb = EvolutionSandbox(n_steps=5, gate=_AlwaysPassGate())
    rep = sb.run()
    if rep.accepted_steps > 0:
        clone_hashes = {s.clone_hash for s in rep.steps
                        if s.outcome is StepOutcome.ACCEPTED}
        assert rep.best_clone_hash in clone_hashes


# ---------------------------------------------------------------------------
# Hygiene
# ---------------------------------------------------------------------------


def test_n_steps_must_be_positive() -> None:
    with pytest.raises(ValueError):
        EvolutionSandbox(n_steps=0, gate=_AlwaysPassGate())
