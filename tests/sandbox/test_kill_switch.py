"""Tests for the v2.0 kill switch (Aufgabe 5)."""
from __future__ import annotations

from dataclasses import dataclass

from desi.sandbox import (
    EvolutionSandbox,
    GateVerdict,
    ShadowLedgerEventType,
    StepOutcome,
)


@dataclass
class _PassGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=True, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
        )


class _PrecisionRegressionGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=False, precision=0.98, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
            failure_reason="precision=0.98 != 1.000",
        )


class _AuthorityRegressionGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=False, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=9, tool_precision=1.0, hash_mismatches=0,
            failure_reason="authority_blocks=9 != 10",
        )


class _HashMismatchGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=False, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=1,
            failure_reason="hash_mismatches=1 != 0",
        )


class _ChaoticGate:
    """Raises a different exception every call to exercise the
    catch-all kill path."""

    def __init__(self) -> None:
        self._n = 0

    def evaluate(self) -> GateVerdict:
        self._n += 1
        if self._n % 3 == 0:
            raise ZeroDivisionError("simulated")
        if self._n % 3 == 1:
            raise KeyError("simulated")
        raise RuntimeError("simulated")


def test_precision_regression_is_rejected_not_killed() -> None:
    sb = EvolutionSandbox(n_steps=2, gate=_PrecisionRegressionGate())
    rep = sb.run()
    assert rep.killed_steps == 0
    assert rep.rejected_steps == 2
    assert all(s.failure_reason for s in rep.steps)


def test_authority_regression_is_rejected_not_killed() -> None:
    sb = EvolutionSandbox(n_steps=2, gate=_AuthorityRegressionGate())
    rep = sb.run()
    assert rep.rejected_steps == 2
    for s in rep.steps:
        assert "authority_blocks" in s.failure_reason


def test_hash_mismatch_is_rejected_not_killed() -> None:
    sb = EvolutionSandbox(n_steps=2, gate=_HashMismatchGate())
    rep = sb.run()
    assert rep.rejected_steps == 2
    for s in rep.steps:
        assert "hash_mismatches" in s.failure_reason


def test_kill_switch_records_in_ledger() -> None:
    """A KILLED step must still emit a MUTATION_REJECTED ledger event."""
    sb = EvolutionSandbox(n_steps=2, gate=_ChaoticGate())
    sb.run()
    rejected = sb.ledger.filter(ShadowLedgerEventType.MUTATION_REJECTED)
    assert len(rejected) == 2
    for e in rejected:
        assert e.payload["killed"] is True
        assert e.payload["failure_reason"]


def test_different_exception_types_all_caught() -> None:
    sb = EvolutionSandbox(n_steps=3, gate=_ChaoticGate())
    rep = sb.run()
    assert rep.killed_steps == 3
    seen = {s.failure_reason.split(":")[0] for s in rep.steps}
    # Three distinct exception types should appear.
    assert seen == {"ZeroDivisionError", "KeyError", "RuntimeError"}


def test_sandbox_completes_normally_after_kill() -> None:
    """A run with one KILLED step must still emit SANDBOX_COMPLETED."""
    sb = EvolutionSandbox(n_steps=2, gate=_ChaoticGate())
    sb.run()
    completed = sb.ledger.filter(ShadowLedgerEventType.SANDBOX_COMPLETED)
    assert len(completed) == 1


def test_kill_in_middle_does_not_corrupt_subsequent_step() -> None:
    """If step 2 of 4 kills but step 3 passes, the run still finishes."""

    class _ThirdKill:
        def __init__(self) -> None:
            self._n = 0

        def evaluate(self) -> GateVerdict:
            self._n += 1
            if self._n == 2:
                raise RuntimeError("middle-kill")
            return GateVerdict(
                passed=True, precision=1.0, recall=1.0,
                false_positives=0, authority_blocks=10,
                tool_precision=1.0, hash_mismatches=0,
            )

    sb = EvolutionSandbox(n_steps=4, gate=_ThirdKill())
    rep = sb.run()
    assert rep.killed_steps == 1
    assert rep.accepted_steps == 3
    outcomes = [s.outcome for s in rep.steps]
    assert outcomes == [
        StepOutcome.ACCEPTED, StepOutcome.KILLED,
        StepOutcome.ACCEPTED, StepOutcome.ACCEPTED,
    ]
