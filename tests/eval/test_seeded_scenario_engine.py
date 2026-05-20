"""Tests for v0.9 SeededScenarioEngine — determinism + variance."""
from __future__ import annotations

import pytest

from desi.eval import (
    InstantiatedScenario,
    SeededScenarioEngine,
    seed_variant_scenarios,
)


@pytest.fixture
def engine() -> SeededScenarioEngine:
    return SeededScenarioEngine()


# ---------------------------------------------------------------------------
# Closed registry
# ---------------------------------------------------------------------------


def test_seed_variant_scenarios_is_a_closed_set() -> None:
    ids = seed_variant_scenarios()
    assert ids == ("ADV_BRANCH_EXPLOSION", "S2", "S6")


def test_engine_returns_instantiated_scenario_for_variant(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("ADV_BRANCH_EXPLOSION", 42)
    assert isinstance(inst, InstantiatedScenario)
    assert inst.scenario_id == "ADV_BRANCH_EXPLOSION"
    assert inst.seed == 42


# ---------------------------------------------------------------------------
# Same seed → same trajectory bytes (bit-identical)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_id",
                         ["ADV_BRANCH_EXPLOSION", "S2", "S6"])
def test_same_seed_same_trajectory(
    engine: SeededScenarioEngine, scenario_id: str,
) -> None:
    a = engine.instantiate(scenario_id, 42)
    b = engine.instantiate(scenario_id, 42)
    assert a.trajectory.trajectory_id == b.trajectory.trajectory_id
    assert len(a.trajectory.steps) == len(b.trajectory.steps)
    for s1, s2 in zip(a.trajectory.steps, b.trajectory.steps):
        assert s1.loop_index == s2.loop_index
        assert s1.operator == s2.operator
        assert s1.focus_claim_id == s2.focus_claim_id


@pytest.mark.parametrize("scenario_id",
                         ["ADV_BRANCH_EXPLOSION", "S2", "S6"])
def test_same_seed_same_permutation_id(
    engine: SeededScenarioEngine, scenario_id: str,
) -> None:
    a = engine.instantiate(scenario_id, 42)
    b = engine.instantiate(scenario_id, 42)
    assert a.generation_metadata.permutation_id == \
        b.generation_metadata.permutation_id


# ---------------------------------------------------------------------------
# Different seed → different trajectory
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_id",
                         ["ADV_BRANCH_EXPLOSION", "S2", "S6"])
def test_different_seeds_yield_different_permutation_ids(
    engine: SeededScenarioEngine, scenario_id: str,
) -> None:
    a = engine.instantiate(scenario_id, 42)
    b = engine.instantiate(scenario_id, 43)
    assert a.generation_metadata.permutation_id != \
        b.generation_metadata.permutation_id


def test_adv_branch_explosion_varies_branch_count_across_mandatory_seeds(
    engine: SeededScenarioEngine,
) -> None:
    """The variant generator must produce ≥2 distinct branch counts
    across the mandatory seed list — otherwise the gate's variance
    signal is decorative."""
    counts = set()
    for seed in (42, 43, 44, 45, 46):
        inst = engine.instantiate("ADV_BRANCH_EXPLOSION", seed)
        # Count distinct claim_ids in the trajectory — proxy for
        # branch attempts.
        counts.add(len({s.focus_claim_id for s in inst.trajectory.steps
                         if s.focus_claim_id is not None}))
    assert len(counts) >= 2, (
        f"ADV_BRANCH_EXPLOSION variant produced only one branch count "
        f"across mandatory seeds: {counts}"
    )


# ---------------------------------------------------------------------------
# Static fallthrough for scenarios without a registered variant
# ---------------------------------------------------------------------------


def test_static_scenario_falls_through_with_static_permutation_id(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("S5", 42)
    assert inst.scenario_id == "S5"
    assert inst.generation_metadata.permutation_id == "static"


def test_static_scenario_same_trajectory_across_seeds(
    engine: SeededScenarioEngine,
) -> None:
    a = engine.instantiate("S5", 42)
    b = engine.instantiate("S5", 43)
    assert a.trajectory.trajectory_id == b.trajectory.trajectory_id
    assert len(a.trajectory.steps) == len(b.trajectory.steps)


# ---------------------------------------------------------------------------
# InstantiatedScenario is Scenario-compatible
# ---------------------------------------------------------------------------


def test_instantiated_scenario_quacks_like_scenario(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("S2", 42)
    # Required attributes the harness reads from a Scenario.
    assert hasattr(inst, "scenario_id")
    assert hasattr(inst, "trajectory_factory")
    assert hasattr(inst, "expectation")
    assert hasattr(inst, "pre_run")
    assert hasattr(inst, "post_run")
    # trajectory_factory is callable and returns a Trajectory.
    traj = inst.trajectory_factory()
    assert traj is inst.trajectory  # same object, deterministic


def test_unknown_scenario_id_raises(engine: SeededScenarioEngine) -> None:
    with pytest.raises((KeyError, ValueError, Exception)):
        engine.instantiate("S_DOES_NOT_EXIST", 42)
