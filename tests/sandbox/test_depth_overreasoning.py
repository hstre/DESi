"""Tests for v2.2 overreasoning guard (Aufgabe 6)."""
from __future__ import annotations

from dataclasses import dataclass

from desi.sandbox import (
    DepthEvolutionSandbox,
    DepthImpactMetrics,
    GateVerdict,
    overreasoning_check,
)


@dataclass
class _CleanGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=True, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
        )


def _metrics(*, cycle: float = 1.0, blocked: float = 1.0):
    return DepthImpactMetrics(
        mean_resolution_depth=0.0, max_resolution_depth=0,
        cycle_detection_rate=cycle,
        blocked_propagation_rate=blocked,
        depth_exceeded_rate=0.0, resolution_complete_rate=0.0,
    )


# ---------------------------------------------------------------------------
# Direct unit tests
# ---------------------------------------------------------------------------


def test_no_rejection_when_metrics_improve_with_fitness() -> None:
    v = overreasoning_check(
        prev_metrics=_metrics(cycle=0.5, blocked=0.5),
        new_metrics=_metrics(cycle=1.0, blocked=1.0),
        prev_fitness=4.0, new_fitness=6.0,
        hash_mismatches=0,
    )
    assert v.rejected is False


def test_rejection_when_cycle_decays_for_higher_fitness() -> None:
    v = overreasoning_check(
        prev_metrics=_metrics(cycle=1.0), new_metrics=_metrics(cycle=0.5),
        prev_fitness=5.0, new_fitness=6.0,
        hash_mismatches=0,
    )
    assert v.rejected is True


def test_rejection_when_blocked_decays_for_higher_fitness() -> None:
    v = overreasoning_check(
        prev_metrics=_metrics(blocked=1.0), new_metrics=_metrics(blocked=0.0),
        prev_fitness=5.0, new_fitness=6.0,
        hash_mismatches=0,
    )
    assert v.rejected is True


def test_no_rejection_when_fitness_did_not_grow() -> None:
    """Aufgabe 6 only triggers WHEN fitness grew. Decline + decay is
    a different (separately reported) failure."""
    v = overreasoning_check(
        prev_metrics=_metrics(cycle=1.0), new_metrics=_metrics(cycle=0.5),
        prev_fitness=5.0, new_fitness=5.0,
        hash_mismatches=0,
    )
    assert v.rejected is False


def test_replay_mismatch_always_rejects() -> None:
    v = overreasoning_check(
        prev_metrics=_metrics(), new_metrics=_metrics(),
        prev_fitness=5.0, new_fitness=5.0,
        hash_mismatches=1,
    )
    assert v.rejected is True


# ---------------------------------------------------------------------------
# End-to-end: stable run does not trigger overreasoning rejection
# ---------------------------------------------------------------------------


def test_clean_run_has_no_overreasoning_rejections() -> None:
    """With a clean gate the cycle/blocked rates from the stress
    suite are constant across all max_depth values, so the guard
    cannot fire."""
    sb = DepthEvolutionSandbox(start_depth=3, n_steps=30,
                                gate=_CleanGate())
    rep = sb.run()
    overreasoning = [s for s in rep.steps if "cycle" in s.failure_reason
                     or "blocked" in s.failure_reason]
    assert overreasoning == []
