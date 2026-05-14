"""Tests for the seven shipped scenarios."""
from __future__ import annotations

import pytest

from desi.eval import SCENARIOS, list_scenarios, scenario_by_id


def test_list_scenarios_returns_seven() -> None:
    assert len(list_scenarios()) == 7


def test_scenario_ids_are_S1_to_S7() -> None:
    ids = sorted(s.scenario_id for s in SCENARIOS)
    assert ids == ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]


def test_scenario_by_id_returns_matching() -> None:
    assert scenario_by_id("S2").name == "contradictory_claims"


def test_scenario_by_id_unknown_raises() -> None:
    with pytest.raises(KeyError):
        scenario_by_id("S99")


@pytest.mark.parametrize("scenario", list_scenarios(),
                          ids=lambda s: s.scenario_id)
def test_each_scenario_has_a_well_formed_trajectory(scenario) -> None:
    traj = scenario.trajectory_factory()
    assert traj.trajectory_id
    assert len(traj.steps) >= 1
    # Operators are normalised strings.
    for step in traj.steps:
        assert isinstance(step.operator, str)
        assert step.operator


@pytest.mark.parametrize("scenario", list_scenarios(),
                          ids=lambda s: s.scenario_id)
def test_each_scenario_has_an_expectation_block(scenario) -> None:
    exp = scenario.expectation
    # At least one verifiable assertion or a notes-only marker.
    has_assertion = (
        bool(exp.required_claim_ids)
        or bool(exp.required_relation_types)
        or bool(exp.forbidden_relation_types)
        or bool(exp.min_event_counts)
    )
    assert has_assertion or exp.notes
