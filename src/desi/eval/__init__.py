"""Evaluation harness + scenario library.

v0.4 introduces a standardised test framework: a deterministic
:class:`EvaluationHarness` that runs scenarios against DESi while
capturing the live observation stream and the memory state.

The harness is observation-only. No new operators, no new guards, no
DESi-source change. The seven shipped scenarios (S1..S7) probe
specific structural patterns DESi should produce on well-defined
problem classes.
"""
from __future__ import annotations

from .harness import (
    EvaluationHarness,
    EvaluationResult,
    config_hash,
)
from .scenarios import (
    SCENARIOS,
    Scenario,
    ScenarioExpectation,
    list_scenarios,
    scenario_by_id,
)

__all__ = [
    "EvaluationHarness",
    "EvaluationResult",
    "SCENARIOS",
    "Scenario",
    "ScenarioExpectation",
    "config_hash",
    "list_scenarios",
    "scenario_by_id",
]
