"""Tests for v2.2 plateau detection (Aufgabe 8)."""
from __future__ import annotations

from dataclasses import dataclass

from desi.sandbox import (
    DepthEvolutionSandbox,
    GateVerdict,
    detect_plateau,
)


@dataclass
class _CleanGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=True, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
        )


def test_plateau_function_window_default_is_five() -> None:
    history = [3.0, 3.0, 3.0, 3.0, 3.0]
    assert detect_plateau(history) is True


def test_plateau_detected_in_real_30_step_run() -> None:
    """Given a clean gate, fitness is flat across all max_depth
    values, so a plateau should be detected."""
    sb = DepthEvolutionSandbox(start_depth=3, n_steps=30,
                                gate=_CleanGate())
    rep = sb.run()
    # With flat fitness the plateau detector must fire.
    assert rep.plateau_detected is True


def test_plateau_does_not_stop_the_run() -> None:
    """Even after plateau is detected, the sandbox continues to
    n_steps."""
    sb = DepthEvolutionSandbox(start_depth=3, n_steps=30,
                                gate=_CleanGate())
    rep = sb.run()
    assert rep.total_steps == 30
    assert rep.plateau_detected is True


def test_plateau_recorded_alongside_oscillation() -> None:
    """Both plateau and oscillation flags can be true at once —
    they describe different facets of the same flat-fitness run."""
    sb = DepthEvolutionSandbox(start_depth=3, n_steps=30,
                                gate=_CleanGate())
    rep = sb.run()
    assert rep.plateau_detected is True
    # The deterministic walk over 30 steps reverses direction
    # multiple times.
    assert rep.oscillation_detected is True
